# 分析服务测试占位文件，后续用于验证 AI 分析流程。
from unittest.mock import MagicMock, patch

import pytest
from app.agents.analysis_agent import AnalysisAgent


# =====================================================================
# 测试场景 2：正常流测试（验证大模型返回标准 JSON 时，Agent 能否正确解析）
# =====================================================================
@patch("app.agents.analysis_agent.AsyncOpenAI")  # 拦截 Agent 内部的 AsyncOpenAI 客户端
@pytest.mark.asyncio
async def test_generate_analysis_success(MockAsyncOpenAI):
    # 1. 创建大模型客户端的替身
    mock_client_instance = MockAsyncOpenAI.return_value

    # 2. 模拟大模型返回符合 V4.1 核心要求的标准 JSON 字符串
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""{
            "summary": "本节主要介绍了数据库第三范式的核心定义。",
            "key_concepts": ["3NF", "传递函数依赖"],
            "terms": [{"fr": "3NF", "zh": "第三范式", "explanation": "消除传递依赖"}],
            "highlights": ["重点是理解传递依赖"],
            "source_refs": [{"page": 5, "title": "Normalisation"}]
        }"""
            )
        )
    ]

    # 3. 将这个假回复绑定到 mock 客户端的异步方法上
    mock_client_instance.chat.completions.create.return_value = mock_response

    # 4. 初始化 Agent 并传入假的 API Key（不连网，随便填）
    agent = AnalysisAgent(api_key="sk-fake-key-for-test")

    # 5. 执行解析方法
    context_text = "Chaque déterminant non clé doit être une clé primaire..."
    result = await agent.generate_analysis(context_text)

    # 6. 开始断言（验证结果是否完美对应）
    assert isinstance(result, dict)  # 验证输出必须是 Python 字典
    assert result["summary"] == "本节主要介绍了数据库第三范式的核心定义。"
    assert "3NF" in result["key_concepts"]
    assert result["terms"][0]["fr"] == "3NF"

    # 7. 验证底层调用时是否开启了强管控的 json_object 模式
    mock_client_instance.chat.completions.create.assert_called_once()
    called_kwargs = mock_client_instance.chat.completions.create.call_args[1]
    assert called_kwargs["response_format"] == {"type": "json_object"}
    assert called_kwargs["temperature"] == 0.3


# =====================================================================
# 测试场景 4：异常流测试（验证大模型意外吐出损坏的 JSON 时，系统能否安全捕获）
# =====================================================================
@patch("app.agents.analysis_agent.AsyncOpenAI")
@pytest.mark.asyncio
async def test_generate_analysis_json_error(MockAsyncOpenAI):
    mock_client_instance = MockAsyncOpenAI.return_value
    mock_response = MagicMock()

    # 故意让大模型返回一个残缺的、不合法的 JSON 字符串（少了大括号）
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"summary": "残缺的JSON"'))
    ]
    mock_client_instance.chat.completions.create.return_value = mock_response

    agent = AnalysisAgent(api_key="sk-fake-key-for-test")

    # 验证当 JSON 解析失败时，Agent 是否如期抛出了自定义的 RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        await agent.generate_analysis("Some context")

    assert "大模型生成的格式不正确" in str(exc_info.value)


# =====================================================================
# 测试场景 ？：安全边界测试（验证未配置 API Key 时，Agent 能否及时拦截报错）
# =====================================================================
@patch.dict(
    "os.environ", {}, clear=True
)  # 清空临时环境变量，模拟完全没有密钥的极端环境
def test_analysis_agent_missing_api_key():
    # 当不传参数且环境没有密钥时，初始化应该直接抛出 ValueError，防止后续白白浪费算力
    with pytest.raises(ValueError) as exc_info:
        AnalysisAgent(api_key=None)

    assert "API Key 未配置" in str(exc_info.value)


# =====================================================================
# 测试场景 1：直接展示已有的小节解析记录（命中本地缓存，不调用大模型）
# =====================================================================
@patch("app.services.analysis_service.analysis_repository")  # 拦截数据库持久层
@patch("app.agents.analysis_agent.AsyncOpenAI")  # 拦截大模型底层的网络请求
@pytest.mark.asyncio
async def test_display_existing_analysis_from_db(MockAsyncOpenAI, mock_repo):
    """
    Scénario 1 : Charger une analyse existante depuis la base de données SQLite.
    L'API OpenAI ne doit pas être appelée si l'analyse existe déjà.
    """
    # 1. Configuration du mock de la base de données pour simuler une analyse existante
    # 模拟数据库中已经存在该小节的解析数据
    mock_exist_analysis = {
        "id": "existing-uuid-1234",
        "document_id": "doc_001",
        "section_id": "sec_001",
        "analysis_type": AnalysisType.SECTION,
        "language": "fr-zh",
        "content_markdown": "## Analyse existante...",
        "content_json": {"summary": "Résumé existant"},
    }
    mock_repo.get_analysis_by_node.return_value = mock_exist_analysis

    # 2. Initialisation du service avec les dépendances mockées
    service = AnalysisService(repository=mock_repo)

    # 3. Exécution de la méthode principale du service
    result = await service.get_or_generate_section_analysis(
        document_id="doc_001", section_id="sec_001"
    )

    # 4. Assertions : Vérifier que les données proviennent bien de la BDD
    # 断言：系统直接返回了数据库中的老数据，没有走创建流程
    assert result.id == "existing-uuid-1234"
    assert result.content_json["summary"] == "Résumé existant"

    # 5. Vérification CRITIQUE : L'API OpenAI ne doit JAMAIS être appelée
    # 关键断言：大模型替身从未被调用过，成功为用户节省了 Token 额度
    mock_client_instance = MockAsyncOpenAI.return_value
    mock_client_instance.chat.completions.create.assert_not_called()


# =====================================================================
# 测试场景 3：当前小节原文过少时，系统自动检索并合并相邻兄弟节点的原文
# =====================================================================
@patch("app.services.analysis_service.analysis_repository")
@patch("app.agents.analysis_agent.AsyncOpenAI")
@pytest.mark.asyncio
async def test_fallback_to_sibling_chunks_when_text_insufficient(
    MockAsyncOpenAI, mock_repo
):
    """
    Scénario 3 : Compléter le contexte avec les nœuds frères si le texte du nœud actuel est trop court.
    验证当前小节字数过少（低于阈值）时，系统是否会自动触发兄弟节点内容的补全和合并。
    """
    # 1. Simulation d'un texte trop court pour le nœud actuel (seulement 50 caractères)
    # 模拟当前选中小节在数据库里只有极少的原文（触发不足阈值）
    mock_repo.get_chunks_by_node.return_value = [
        MagicMock(content="Introduction courte.", page_number=2)
    ]

    # 2. Simulation des chunks des nœuds frères (le contexte de rechange)
    # 模拟数据库返回的同级兄弟小节的丰富原文内容
    mock_repo.get_neighbor_sibling_chunks.return_value = [
        MagicMock(
            content="Contenu détaillé du nœud frère qui complète l'explication.",
            page_number=3,
        )
    ]

    # 3. Configuration de la réponse de l'IA pour le flux normal
    mock_client_instance = MockAsyncOpenAI.return_value
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"summary": "Analyse fusionnée"}'))
    ]
    mock_client_instance.chat.completions.create.return_value = mock_response

    # 4. Exécution du service
    service = AnalysisService(repository=mock_repo)
    await service.get_or_generate_section_analysis(
        document_id="doc_001", section_id="sec_001"
    )

    # 5. Assertions sur l'orchestration des données
    # 断言 1：系统必须因为内容不足而前往数据库捞取了兄弟节点的数据
    mock_repo.get_neighbor_sibling_chunks.assert_called_once_with("sec_001")

    # 6. Vérification du prompt envoyé à l'IA
    # 断言 2：验证送给大模型的最终大文本里，是否已经把当前内容和兄弟内容完美拼接在了一起
    called_args = mock_client_instance.chat.completions.create.call_args[1]
    user_message = called_args["messages"][1]["content"]

    assert "Introduction courte." in user_message
    assert "Contenu détaillé du nœud frère" in user_message
