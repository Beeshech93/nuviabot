import pytest
from app.schemas.ai import AIGenerateRequest
from app.services.ai_service import ai_service


@pytest.mark.asyncio
async def test_ai_generation_spanish():
    req = AIGenerateRequest(
        business_name="Aura Luxe",
        industry="Cosméticos Orgánicos",
        product_service="Serum Facial Reparador",
        target_audience="Mujeres de 25-45 años",
        social_network="instagram",
        language="es",
        tone="professional",
        objective="sales",
        variations_count=2,
    )
    result = await ai_service.generate_content(req)
    assert len(result.proposals) >= 2
    assert result.language == "es"
    first = result.proposals[0]
    assert len(first.caption) > 20
    assert len(first.hashtags) > 0


@pytest.mark.asyncio
async def test_ai_generation_haitian_creole():
    req = AIGenerateRequest(
        business_name="Bel Lakay",
        industry="Konstriksyon & Dekorasyon",
        product_service="Materyo Pwofesyonèl",
        target_audience="Pwopryetè kay ak enjenyè",
        social_network="facebook",
        language="ht",
        tone="energetic",
        objective="community",
        variations_count=2,
    )
    result = await ai_service.generate_content(req)
    assert len(result.proposals) >= 2
    assert result.language == "ht"
    assert "biznis" in result.proposals[0].caption.lower() or "materyo" in result.proposals[0].caption.lower() or "lakay" in result.proposals[0].caption.lower() or "rezilta" in result.proposals[0].caption.lower()


@pytest.mark.asyncio
async def test_ai_improve_caption():
    original = "Tenemos un nuevo producto disponible en nuestra tienda hoy."
    result = await ai_service.improve_caption(
        original=original,
        instruction="Hazlo más llamativo con emojis y llamada a comentar",
        language="es",
    )
    assert len(result.improved_caption) > len(original)
    assert "comenta" in result.improved_caption.lower() or "👇" in result.improved_caption or "🔥" in result.improved_caption


@pytest.mark.asyncio
async def test_ai_hashtags_generation():
    result = await ai_service.generate_hashtags(
        content="Lanzamiento de nueva colección de moda sostenible",
        social_network="instagram",
        industry="ModaSostenible",
    )
    assert len(result.hashtags) >= 5
    assert any("ModaSostenible" in h for h in result.hashtags)


@pytest.mark.asyncio
async def test_ai_chat_assistant():
    # Spanish chat test
    res_es = await ai_service.chat_assistant("¿Cómo hago un buen video para TikTok?", language="es")
    assert "TikTok" in res_es.reply
    assert len(res_es.suggested_actions) > 0

    # Haitian Creole chat test
    res_ht = await ai_service.chat_assistant("Kijan pou mwen ogmante entèraksyon sou TikTok?", language="ht")
    assert "TikTok" in res_ht.reply
    assert "segonn" in res_ht.reply.lower() or "estrateji" in res_ht.reply.lower()


