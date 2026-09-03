from __future__ import annotations

import io
import re
import zipfile
from datetime import UTC, datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from backend.candidate_profile import load_candidate_profile


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Name", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=25, textColor=colors.HexColor("#12372A"), alignment=TA_CENTER, spaceAfter=4))
    styles.add(ParagraphStyle(name="Contact", parent=styles["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#4D625A"), alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#167D5A"), spaceBefore=9, spaceAfter=5))
    styles.add(ParagraphStyle(name="BodyText2", parent=styles["BodyText"], fontSize=9.5, leading=13, textColor=colors.HexColor("#25332E"), spaceAfter=5))
    return styles


def _document(story: list, title: str, author: str) -> bytes:
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title=title, author=author)
    doc.build(story)
    return output.getvalue()


def cv_pdf(job: dict) -> bytes:
    candidate = load_candidate_profile()
    identity = candidate["identity"]
    resume = candidate["resume"]
    name = identity["full_name"]
    styles = _styles()
    story = [
        Paragraph(escape(name), styles["Name"]),
        Paragraph(
            f"{escape(str(resume['title']))}<br/>{escape(str(resume['location']))} | "
            f"{escape(str(identity['email']))} | {escape(str(identity['phone']))}",
            styles["Contact"],
        ),
        Paragraph("PROFESSIONAL SUMMARY", styles["Section"]),
        Paragraph(escape(str(resume["summary"])), styles["BodyText2"]),
        Paragraph("CORE EXPERTISE", styles["Section"]),
        Paragraph(" | ".join(escape(str(skill)) for skill in resume.get("skills", [])), styles["BodyText2"]),
        Paragraph("PROFESSIONAL EXPERIENCE", styles["Section"]),
    ]
    for experience in resume.get("experience", []):
        heading = f"<b>{escape(str(experience['company']))} - {escape(str(experience['title']))}</b> | {escape(str(experience['period']))}"
        highlights = "<br/>".join(escape(str(item)) for item in experience.get("highlights", []))
        story.append(Paragraph(f"{heading}<br/>{highlights}", styles["BodyText2"]))
    story.extend(
        [
            Paragraph("EDUCATION", styles["Section"]),
            Paragraph("<br/>".join(escape(str(item)) for item in resume.get("education", [])), styles["BodyText2"]),
            Paragraph("TARGET POSITION", styles["Section"]),
            Paragraph(
                f"{escape(str(job.get('role', '')))} at {escape(str(job.get('company', '')))}. "
                "This resume emphasizes confirmed experience relevant to the vacancy without adding unverified claims.",
                styles["BodyText2"],
            ),
        ]
    )
    return _document(story, f"CV - {name}", name)


def cover_letter_pdf(job: dict) -> bytes:
    candidate = load_candidate_profile()
    identity = candidate["identity"]
    resume = candidate["resume"]
    name = identity["full_name"]
    styles = _styles()
    company, role = escape(str(job.get("company", "Hiring Team"))), escape(str(job.get("role", "the position")))
    story = [
        Paragraph(escape(name), styles["Name"]),
        Paragraph(
            f"{escape(str(identity['email']))} | {escape(str(identity['phone']))} | {escape(str(resume['location']))}",
            styles["Contact"],
        ),
        Spacer(1, 8 * mm),
        Paragraph(f"Application for {role}", styles["Section"]),
        Paragraph(f"Dear {company} Hiring Team,", styles["BodyText2"]),
        Paragraph(f"I am applying for the {role} position. {escape(str(resume['summary']))}", styles["BodyText2"]),
        Paragraph(escape(str(resume.get("cover_letter_summary", resume["summary"]))), styles["BodyText2"]),
        Paragraph(f"I would welcome the opportunity to discuss how this experience can support {company}'s engineering goals.", styles["BodyText2"]),
        Spacer(1, 5 * mm),
        Paragraph(f"Sincerely,<br/><b>{escape(name)}</b>", styles["BodyText2"]),
    ]
    return _document(story, f"Cover Letter - {company}", name)


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:80] or "job"


def job_info(job: dict) -> str:
    return "\n".join([
        f"Company: {job.get('company', 'UNKNOWN')}", f"Role: {job.get('role', 'UNKNOWN')}",
        f"Job URL: {job.get('link', '')}", f"Source: {job.get('source', 'UNKNOWN')}",
        f"Match score: {job.get('match', 'UNKNOWN')}", f"Report status: {job.get('report_status', 'open')}",
        "Application status: ACTIVE_NOT_APPLIED", f"Generated: {datetime.now(UTC).isoformat()}",
        "Notes: Generated from the AutoApply Report. Unknown vacancy details were not invented.",
    ]) + "\n"


def package_zip(jobs: list[dict]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index, job in enumerate(jobs, start=1):
            folder = f"{index:02d}_{_safe_name(str(job.get('company', '')))}_{_safe_name(str(job.get('role', '')))}"
            archive.writestr(f"{folder}/cv.pdf", cv_pdf(job))
            archive.writestr(f"{folder}/cover_letter.pdf", cover_letter_pdf(job))
            archive.writestr(f"{folder}/infos_job.txt", job_info(job))
    return output.getvalue()
