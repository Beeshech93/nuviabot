from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_organization, get_current_user
from app.db.models import Organization, User
from app.db.session import get_db
from app.schemas.analytics import AnalyticsSummaryResponse, TopPostItem
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    days: int = Query(30, ge=7, le=90),
    client_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Retrieve verified social media metrics. When no accounts connected, returns clear demo/empty indicators."""
    return AnalyticsService.get_summary(
        db, organization_id=org.id, client_id=client_id, days=days
    )


@router.get("/top-posts", response_model=List[TopPostItem])
def get_top_posts(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    return AnalyticsService.get_top_posts(db, organization_id=org.id, limit=limit)


@router.get("/export-csv")
def export_analytics_csv(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    csv_data = AnalyticsService.export_csv(db, organization_id=org.id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=nuvio_analytics_{org.slug}.csv"
        },
    )


@router.get("/report-view")
def export_analytics_report_view(
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Returns a print-ready, executive-grade HTML report suitable for browser print to PDF."""
    summary = AnalyticsService.get_summary(db, organization_id=org.id, days=days)
    top_posts = AnalyticsService.get_top_posts(db, organization_id=org.id, limit=5)
    now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    platform_rows = "".join(
        f"""
        <tr>
            <td style="padding:10px;border-bottom:1px solid #e2e8f0;text-transform:capitalize;font-weight:600;">{p.platform}</td>
            <td style="padding:10px;border-bottom:1px solid #e2e8f0;">{p.followers:,}</td>
            <td style="padding:10px;border-bottom:1px solid #e2e8f0;">{p.impressions:,}</td>
            <td style="padding:10px;border-bottom:1px solid #e2e8f0;">{p.reach:,}</td>
            <td style="padding:10px;border-bottom:1px solid #e2e8f0;">{p.views:,}</td>
            <td style="padding:10px;border-bottom:1px solid #e2e8f0;">{p.likes:,}</td>
            <td style="padding:10px;border-bottom:1px solid #e2e8f0;">{p.comments:,}</td>
            <td style="padding:10px;border-bottom:1px solid #e2e8f0;font-weight:bold;color:#4f46e5;">{p.engagement_rate}%</td>
        </tr>
        """
        for p in summary.by_platform.values()
    )

    posts_rows = "".join(
        f"""
        <div style="padding:12px;border:1px solid #e2e8f0;border-radius:6px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <strong style="color:#1e293b;">{p.title}</strong>
                <span style="font-size:12px;background:#e0e7ff;color:#4338ca;padding:2px 8px;border-radius:4px;text-transform:capitalize;">{p.platform}</span>
            </div>
            <p style="font-size:13px;color:#475569;margin-bottom:6px;">{p.content_snippet}</p>
            <div style="font-size:12px;color:#64748b;">
                ❤️ {p.likes} likes &nbsp;|&nbsp; 💬 {p.comments} comentarios &nbsp;|&nbsp; <strong>{p.engagement_rate}% engagement</strong>
            </div>
        </div>
        """
        for p in top_posts
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Nuvio Growth Bot - Informe Ejecutivo de Redes Sociales</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #0f172a; margin: 40px auto; max-width: 900px; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #4f46e5; padding-bottom: 16px; margin-bottom: 24px; }}
            .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 28px; }}
            .kpi-card {{ border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; background: #f8fafc; }}
            .kpi-val {{ font-size: 22px; font-weight: 800; color: #1e1b4b; }}
            .kpi-lbl {{ font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600; margin-bottom: 4px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 28px; }}
            th {{ background: #f1f5f9; padding: 10px; text-align: left; color: #334155; font-size: 11px; text-transform: uppercase; }}
            @media print {{
                body {{ margin: 0; padding: 10mm; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="no-print" style="margin-bottom: 20px; text-align: right;">
            <button onclick="window.print()" style="background:#4f46e5;color:white;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-weight:600;">🖨️ Imprimir / Guardar como PDF</button>
        </div>

        <div class="header">
            <div>
                <h1 style="margin:0;font-size:24px;color:#1e1b4b;">NUVIO GROWTH BOT</h1>
                <p style="margin:4px 0 0;color:#64748b;font-size:13px;">Informe Ejecutivo de Rendimiento y Crecimiento en Redes Sociales</p>
            </div>
            <div style="text-align:right;">
                <h3 style="margin:0;font-size:16px;color:#334155;">{org.name}</h3>
                <span style="font-size:12px;color:#64748b;">Generado: {now_str} (Últimos {days} días)</span>
            </div>
        </div>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-lbl">Cuentas Conectadas</div>
                <div class="kpi-val">{summary.total_connected_accounts}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Seguidores Totales</div>
                <div class="kpi-val">{summary.total_followers:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Impresiones (30d)</div>
                <div class="kpi-val">{summary.total_impressions:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Interacción Promedio</div>
                <div class="kpi-val">{summary.total_engagement_rate}%</div>
            </div>
        </div>

        <h3 style="font-size:16px;color:#1e293b;margin-bottom:12px;">Rendimiento Desglosado por Plataforma Oficial</h3>
        <table>
            <thead>
                <tr>
                    <th>Plataforma</th>
                    <th>Seguidores</th>
                    <th>Impresiones</th>
                    <th>Alcance</th>
                    <th>Vistas</th>
                    <th>Likes</th>
                    <th>Comentarios</th>
                    <th>Tasa Interacción</th>
                </tr>
            </thead>
            <tbody>
                {platform_rows}
            </tbody>
        </table>

        <h3 style="font-size:16px;color:#1e293b;margin-bottom:12px;">Publicaciones con Mejor Rendimiento</h3>
        {posts_rows}

        <footer style="margin-top:40px;border-top:1px solid #e2e8f0;padding-top:12px;font-size:11px;color:#94a3b8;text-align:center;">
            NUVIO GROWTH BOT — Crecimiento legítimo mediante optimización de contenido, IA y estadísticas oficiales verificadas.
        </footer>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")

