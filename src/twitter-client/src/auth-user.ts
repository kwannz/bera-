import { TwitterAuthOptions, TwitterGuestAuth } from './auth';
import { requestApi } from './api';
import { CookieJar } from 'tough-cookie';
import { updateCookieJar } from './requests';
import { Headers } from 'headers-polyfill';
import { TwitterApiErrorRaw } from './errors';
import { Type, type Static } from '@sinclair/typebox';
import { Check } from '@sinclair/typebox/value';
import * as OTPAuth from 'otpauth';
import { LegacyUserRaw, parseProfile, type Profile } from './profile';

interface TwitterUserAuthFlowInitRequest {
  flow_name: string;
  input_flow_data: Record<string, unknown>;
}

interface TwitterUserAuthFlowSubtaskRequest {
  flow_token: string;
  subtask_inputs: ({
    subtask_id: string;
  } & Record<string, unknown>)[];
}

type TwitterUserAuthFlowRequest =
  | TwitterUserAuthFlowInitRequest
  | TwitterUserAuthFlowSubtaskRequest;

interface TwitterUserAuthFlowResponse {
  errors?: TwitterApiErrorRaw[];
  flow_token?: string;
  status?: string;
  subtasks?: TwitterUserAuthSubtask[];
}

interface TwitterUserAuthVerifyCredentials {
  errors?: TwitterApiErrorRaw[];
}

const TwitterUserAuthSubtask = Type.Object({
  subtask_id: Type.String(),
  enter_text: Type.Optional(Type.Object({})),
});
type TwitterUserAuthSubtask = Static<typeof TwitterUserAuthSubtask>;

type FlowTokenResultSuccess = {
  status: 'success';
  flowToken: string;
  subtask?: TwitterUserAuthSubtask;
};

type FlowTokenResult = FlowTokenResultSuccess | { status: 'error'; err: Error };

/**
 * A user authentication token manager.
 */
export class TwitterUserAuth extends TwitterGuestAuth {
  private userProfile: Profile | undefined;
  private username: string;
  private password: string;
  private email: string;
  private maxRetries = 3;
  private retryDelay = 1000;

  constructor(
    bearerToken: string,
    options?: Partial<TwitterAuthOptions>
  ) {
    super(bearerToken, options);
    this.username = process.env.tusername || '';
    this.password = process.env.tPassword || '';
    this.email = process.env.tEmail || '';
    if (!this.username || !this.password || !this.email) {
      throw new Error('Twitter credentials not available');
    }
  }

  async isLoggedIn(): Promise<boolean> {
    try {
      const res = await requestApi<TwitterUserAuthVerifyCredentials>(
        'https://api.twitter.com/1.1/account/verify_credentials.json',
        this,
      );
      if (!res.success) {
        return false;
      }

      const { value: verify } = res;
      this.userProfile = parseProfile(
        verify as LegacyUserRaw,
        (verify as unknown as { verified: boolean }).verified,
      );
      return verify && !verify.errors?.length;
    } catch {
      return false;
    }
  }

  async me(): Promise<Profile | undefined> {
    if (this.userProfile) {
      return this.userProfile;
    }
    await this.isLoggedIn();
    return this.userProfile;
  }

  private async retryWithDelay<T>(
    operation: () => Promise<T>,
    retryCount = 0
  ): Promise<T> {
    try {
      return await operation();
    } catch (error) {
      if (retryCount < this.maxRetries) {
        await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, retryCount)));
        return this.retryWithDelay(operation, retryCount + 1);
      }
      throw error;
    }
  }

  async login(
    username: string = this.username,
    password: string = this.password,
    email: string = this.email,
    twoFactorSecret?: string,
    appKey?: string,
    appSecret?: string,
    accessToken?: string,
    accessSecret?: string
  ): Promise<void> {
    if (!username || !password || !email) {
      throw new Error('Twitter credentials not available');
    }

    try {
      await super.login();
      let next = await this.initLogin();
      
      try {
        let flow = await this.handleJsInstrumentationSubtask(next as FlowTokenResultSuccess);
        if ('err' in flow) throw flow.err;
        
        flow = await this.handleEnterUserIdentifierSSO(flow as FlowTokenResultSuccess, username);
        if ('err' in flow) throw flow.err;
        
        flow = await this.handleEnterPassword(flow as FlowTokenResultSuccess, password);
        if ('err' in flow) throw flow.err;
        
        if ('subtask' in flow && flow.subtask?.subtask_id === 'AccountDuplicationCheck') {
          flow = await this.handleAccountDuplicationCheck(flow as FlowTokenResultSuccess);
          if ('err' in flow) throw flow.err;
        }
        
        if ('subtask' in flow && flow.subtask?.subtask_id === 'LoginTwoFactorAuthChallenge' && twoFactorSecret) {
          flow = await this.handleTwoFactorAuthChallenge(flow as FlowTokenResultSuccess, twoFactorSecret);
          if ('err' in flow) throw flow.err;
        }
        
        if ('subtask' in flow && flow.subtask?.subtask_id === 'LoginSuccessSubtask') {
          await this.handleSuccessSubtask(flow as FlowTokenResultSuccess);
        } else {
          throw new Error('Login flow did not complete successfully');
        }

        if (appKey && appSecret && accessToken && accessSecret) {
          this.loginWithV2(appKey, appSecret, accessToken, accessSecret);
        }
      } catch (error) {
        throw new Error(`Login failed: ${error instanceof Error ? error.message : String(error)}`);
      }
  }

  async logout(): Promise<void> {
    if (!this.isLoggedIn()) {
      return;
    }

    await requestApi<void>(
      'https://api.twitter.com/1.1/account/logout.json',
      this,
      'POST',
    );
    this.deleteToken();
    this.jar = new CookieJar();
  }

  async installCsrfToken(headers: Headers): Promise<void> {
    const cookies = await this.getCookies();
    const xCsrfToken = cookies.find((cookie) => cookie.key === 'ct0');
    if (xCsrfToken) {
      headers.set('x-csrf-token', xCsrfToken.value);
    }
  }

  async installTo(headers: Headers): Promise<void> {
    headers.set('authorization', `Bearer ${this.bearerToken}`);
    headers.set('cookie', await this.getCookieString());
    await this.installCsrfToken(headers);
  }

  private async initLogin() {
    // Reset certain session-related cookies because Twitter complains sometimes if we don't
    this.removeCookie('twitter_ads_id=');
    this.removeCookie('ads_prefs=');
    this.removeCookie('_twitter_sess=');
    this.removeCookie('zipbox_forms_auth_token=');
    this.removeCookie('lang=');
    this.removeCookie('bouncer_reset_cookie=');
    this.removeCookie('twid=');
    this.removeCookie('twitter_ads_idb=');
    this.removeCookie('email_uid=');
    this.removeCookie('external_referer=');
    this.removeCookie('ct0=');
    this.removeCookie('aa_u=');

    return await this.executeFlowTask({
      flow_name: 'login',
      input_flow_data: {
        flow_context: {
          debug_overrides: {},
          start_location: {
            location: 'splash_screen',
          },
        },
      },
    });
  }

  private async handleJsInstrumentationSubtask(prev: FlowTokenResultSuccess) {
    return await this.executeFlowTask({
      flow_token: prev.flowToken,
      subtask_inputs: [
        {
          subtask_id: 'LoginJsInstrumentationSubtask',
          js_instrumentation: {
            response: '{}',
            link: 'next_link',
          },
        },
      ],
    });
  }

  private async handleEnterAlternateIdentifierSubtask(
    prev: FlowTokenResultSuccess,
    email: string,
  ) {
    return await this.executeFlowTask({
      flow_token: prev.flowToken,
      subtask_inputs: [
        {
          subtask_id: 'LoginEnterAlternateIdentifierSubtask',
          enter_text: {
            text: email,
            link: 'next_link',
          },
        },
      ],
    });
  }

  private async handleEnterUserIdentifierSSO(
    prev: FlowTokenResultSuccess,
    username: string,
  ) {
    return await this.executeFlowTask({
      flow_token: prev.flowToken,
      subtask_inputs: [
        {
          subtask_id: 'LoginEnterUserIdentifierSSO',
          settings_list: {
            setting_responses: [
              {
                key: 'user_identifier',
                response_data: {
                  text_data: { result: username },
                },
              },
            ],
            link: 'next_link',
          },
        },
      ],
    });
  }

  private async handleEnterPassword(
    prev: FlowTokenResultSuccess,
    password: string,
  ) {
    return await this.executeFlowTask({
      flow_token: prev.flowToken,
      subtask_inputs: [
        {
          subtask_id: 'LoginEnterPassword',
          enter_password: {
            password,
            link: 'next_link',
          },
        },
      ],
    });
  }

  private async handleAccountDuplicationCheck(prev: FlowTokenResultSuccess) {
    return await this.executeFlowTask({
      flow_token: prev.flowToken,
      subtask_inputs: [
        {
          subtask_id: 'AccountDuplicationCheck',
          check_logged_in_account: {
            link: 'AccountDuplicationCheck_false',
          },
        },
      ],
    });
  }

  private async handleTwoFactorAuthChallenge(
    prev: FlowTokenResultSuccess,
    secret: string,
  ) {
    const totp = new OTPAuth.TOTP({ secret });
    let error;
    for (let attempts = 1; attempts < 4; attempts += 1) {
      try {
        return await this.executeFlowTask({
          flow_token: prev.flowToken,
          subtask_inputs: [
            {
              subtask_id: 'LoginTwoFactorAuthChallenge',
              enter_text: {
                link: 'next_link',
                text: totp.generate(),
              },
            },
          ],
        });
      } catch (err) {
        error = err;
        await new Promise((resolve) => setTimeout(resolve, 2000 * attempts));
      }
    }
    throw error;
  }

  private async handleAcid(
    prev: FlowTokenResultSuccess,
    email: string | undefined,
  ) {
    return await this.executeFlowTask({
      flow_token: prev.flowToken,
      subtask_inputs: [
        {
          subtask_id: 'LoginAcid',
          enter_text: {
            text: email,
            link: 'next_link',
          },
        },
      ],
    });
  }

  private async handleSuccessSubtask(prev: FlowTokenResultSuccess) {
    return await this.executeFlowTask({
      flow_token: prev.flowToken,
      subtask_inputs: [],
    });
  }

  private async executeFlowTask(
    data: TwitterUserAuthFlowRequest,
    retryCount = 0,
    maxRetries = 3
  ): Promise<FlowTokenResult> {
    const onboardingTaskUrl =
      'https://api.twitter.com/1.1/onboarding/task.json';

    const token = this.guestToken;
    if (token == null) {
      throw new Error('Authentication token is null or undefined.');
    }

    const headers = new Headers({
      authorization: `Bearer ${this.bearerToken}`,
      cookie: await this.getCookieString(),
      'content-type': 'application/json',
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'x-guest-token': token,
      'x-twitter-auth-type': 'OAuth2Client',
      'x-twitter-active-user': 'yes',
      'x-twitter-client-language': 'en',
      'accept': '*/*',
      'accept-language': 'en-US,en;q=0.9',
      'origin': 'https://twitter.com',
      'referer': 'https://twitter.com/',
      'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="120", "Chromium";v="120"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': '"macOS"',
      'sec-fetch-dest': 'empty',
      'sec-fetch-mode': 'cors',
      'sec-fetch-site': 'same-site',
      'x-csrf-token': await this.getCsrfToken(),
      'x-twitter-client-version': 'web/2.0.0'
    });

    try {
      const res = await this.fetch(onboardingTaskUrl, {
        credentials: 'include',
        method: 'POST',
        headers: headers,
        body: JSON.stringify(data),
      });

      await updateCookieJar(this.jar, res.headers);

      if (!res.ok) {
        const errorText = await res.text();
        if (retryCount < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, retryCount) * 1000));
          return this.executeFlowTask(data, retryCount + 1, maxRetries);
        }
        return { status: 'error', err: new Error(errorText) };
      }

      const flow: TwitterUserAuthFlowResponse = await res.json();
      
      if (flow?.flow_token == null || typeof flow.flow_token !== 'string') {
        return { status: 'error', err: new Error('Invalid flow token') };
      }

      if (flow.errors?.length) {
        const error = flow.errors[0];
        if (retryCount < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, retryCount) * 1000));
          return this.executeFlowTask(data, retryCount + 1, maxRetries);
        }
        return {
          status: 'error',
          err: new Error(`Authentication error (${error.code}): ${error.message}`),
        };
      }

      const subtask = flow.subtasks?.length ? flow.subtasks[0] : undefined;
      Check(TwitterUserAuthSubtask, subtask);

      if (subtask?.subtask_id === 'DenyLoginSubtask' && retryCount < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, retryCount) * 1000));
        return this.executeFlowTask(data, retryCount + 1, maxRetries);
      }

      return {
        status: 'success',
        subtask,
        flowToken: flow.flow_token,
      };
    } catch (error) {
      if (retryCount < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, retryCount) * 1000));
        return this.executeFlowTask(data, retryCount + 1, maxRetries);
      }
      return { 
        status: 'error', 
        err: error instanceof Error ? error : new Error(String(error))
      };
    }
  }
}
