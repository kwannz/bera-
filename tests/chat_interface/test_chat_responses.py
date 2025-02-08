import pytest


@pytest.mark.asyncio
async def test_bera_price_query(chat_handler):
    """测试BERA价格查询"""
    handler = await chat_handler
    message = "现在$BERA流通量多少，价格多少"
    response = await handler.process_message("test_session", message)
    assert isinstance(response, dict)
    assert "market_data" in response
    assert "📈 当前价格" in response["market_data"]
    assert "💰 24小时交易量" in response["market_data"]


@pytest.mark.asyncio
async def test_ido_performance_query(chat_handler):
    """测试IDO项目收益查询"""
    handler = await chat_handler
    message = "最近IDO的项目结果如何，收益高吗？"
    response = await handler.process_message("test_session", message)
    assert isinstance(response, dict)
    assert "news" in response
    assert "sentiment" in response


@pytest.mark.asyncio
async def test_pol_explanation_query(chat_handler):
    """测试POL解释查询"""
    handler = await chat_handler
    message = "能不能简单解释一下什么叫POL，我应该怎么参与？"
    response = await handler.process_message("test_session", message)
    assert isinstance(response, dict)
    assert "ai_response" in response
    assert len(response["ai_response"]) > 0


@pytest.mark.asyncio
async def test_bgt_mining_query(chat_handler):
    """测试BGT挖矿建议查询"""
    handler = await chat_handler
    message = "我如果想尽可能的无损参与$BGT挖矿，有什么好建议吗？"
    response = await handler.process_message("test_session", message)
    assert isinstance(response, dict)
    assert "ai_response" in response
    assert len(response["ai_response"]) > 0


@pytest.mark.asyncio
async def test_meme_token_query(chat_handler):
    """测试MeMe Token推荐查询"""
    handler = await chat_handler
    message = "最近有啥值得购买的MeMe Token吗？"
    response = await handler.process_message("test_session", message)
    assert isinstance(response, dict)
    assert "news" in response
    assert "sentiment" in response


@pytest.mark.asyncio
async def test_bera_price_analysis_query(chat_handler):
    """测试BERA价格分析查询"""
    handler = await chat_handler
    message = "你觉得$BERA的价格是否合理，未来怎么看？"
    response = await handler.process_message("test_session", message)
    assert isinstance(response, dict)
    assert "market_data" in response
    assert "sentiment" in response


@pytest.mark.asyncio
async def test_bgt_holding_query(chat_handler):
    """测试BGT持有建议查询"""
    handler = await chat_handler
    message = "我为何要持有$BGT，是不是应该直接换成$BERA卖掉？"
    response = await handler.process_message("test_session", message)
    assert isinstance(response, dict)
    assert "ai_response" in response
    assert "sentiment" in response


@pytest.mark.asyncio
async def test_bgt_delegation_query(chat_handler):
    """测试BGT委托节点查询"""
    handler = await chat_handler
    message = "有哪些节点值得我委托$BGT吗？"
    response = await handler.process_message("test_session", message)
    assert isinstance(response, dict)
    assert "ai_response" in response


@pytest.mark.asyncio
async def test_nft_projects_query(chat_handler):
    """测试NFT项目推荐查询"""
    handler = await chat_handler
    message = "现在有哪些NFT项目值得关注，为什么？"
    response = await handler.process_message("test_session", message)
    assert isinstance(response, dict)
    assert "news" in response
    assert "ai_response" in response


@pytest.mark.asyncio
async def test_lending_pool_query(chat_handler):
    """测试借贷池利率查询"""
    handler = await chat_handler
    message = "现在利率最低的借贷池是哪个？"
    response = await handler.process_message("test_session", message)
    assert isinstance(response, dict)
    assert "market_data" in response
    assert "ai_response" in response


@pytest.mark.asyncio
async def test_berawar_project_query(chat_handler):
    """测试BeraWar项目介绍查询"""
    handler = await chat_handler
    message = "BeraWar是个怎么样的项目，能否给我介绍一下？"
    response = await handler.process_message("test_session", message)
    assert isinstance(response, dict)
    assert "news" in response
    assert "ai_response" in response


@pytest.mark.asyncio
async def test_ai_projects_query(chat_handler):
    """测试AI项目推荐查询"""
    handler = await chat_handler
    message = "现在链上还有别的值得关注的AI项目吗？"
    response = await handler.process_message("test_session", message)
    assert isinstance(response, dict)
    assert "news" in response
    assert "ai_response" in response
