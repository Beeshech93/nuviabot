def test_post_lifecycle_and_human_approval(client, auth_headers, editor_auth_headers):
    # 1. Editor creates a draft post
    create_res = client.post(
        "/api/v1/posts",
        headers=editor_auth_headers,
        json={
            "title": "Post de Prueba para Aprobación",
            "content": "Contenido estratégico generado para Instagram y TikTok. #Marketing #Growth",
            "target_platforms": ["instagram", "tiktok"],
            "submit_for_approval": False,
        },
    )
    assert create_res.status_code == 200
    post = create_res.json()
    post_id = post["id"]
    assert post["status"] == "draft"

    # 2. Cannot publish unapproved post without approval (Strict Human Approval Rule)
    pub_res = client.post(
        f"/api/v1/posts/{post_id}/publish-now",
        headers=editor_auth_headers,
    )
    assert pub_res.status_code == 403
    assert "Human approval is mandatory" in pub_res.json()["detail"]

    # 3. Submit post for approval
    submit_res = client.post(
        f"/api/v1/posts/{post_id}/submit-approval?comments=Revisar por favor",
        headers=editor_auth_headers,
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "pending_approval"

    # 4. Check that post appears in pending approvals list
    pending_res = client.get("/api/v1/approvals/pending", headers=auth_headers)
    assert pending_res.status_code == 200
    pending_ids = [p["id"] for p in pending_res.json()]
    assert post_id in pending_ids

    # 5. Admin approves post
    review_res = client.post(
        f"/api/v1/approvals/{post_id}/review",
        headers=auth_headers,
        json={"action": "approved", "comments": "Aprobado para publicación inmediata"},
    )
    assert review_res.status_code == 200
    assert review_res.json()["status"] in ["approved", "scheduled"]

    # 6. Once approved, publication proceeds
    final_pub = client.post(
        f"/api/v1/posts/{post_id}/publish-now",
        headers=auth_headers,
    )
    assert final_pub.status_code == 200
    assert final_pub.json()["success"] is True
    assert final_pub.json()["status"] == "published"


def test_reject_post_with_feedback(client, auth_headers, editor_auth_headers):
    # 1. Create post and submit for approval directly
    create_res = client.post(
        "/api/v1/posts",
        headers=editor_auth_headers,
        json={
            "title": "Post que será rechazado",
            "content": "Texto preliminar incompleto",
            "target_platforms": ["facebook"],
            "submit_for_approval": True,
        },
    )
    assert create_res.status_code == 200
    post_id = create_res.json()["id"]
    assert create_res.json()["status"] == "pending_approval"

    # 2. Admin rejects with feedback
    reject_res = client.post(
        f"/api/v1/approvals/{post_id}/review",
        headers=auth_headers,
        json={"action": "rejected", "comments": "El texto requiere llamada a la acción clara"},
    )
    assert reject_res.status_code == 200
    data = reject_res.json()
    assert data["status"] == "rejected"
    assert data["rejection_reason"] == "El texto requiere llamada a la acción clara"

