export interface TwitterError {
  code: number;
  message: string;
}

export interface TwitterResponse<T> {
  data?: T;
  errors?: TwitterError[];
}

export interface TwitterUser {
  id: string;
  name: string;
  username: string;
  verified: boolean;
}

export interface TweetV2 {
  id: string;
  text: string;
}

export interface TweetV2Response {
  data: TweetV2;
}

export interface TwitterTweet {
  id: string;
  text: string;
  created_at: string;
  author_id: string;
}
