#!/usr/bin/env python3
"""Generate cv.typ from the current Chinese resume pages."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


def read_file(path: Path) -> str:
    """Read a markdown file and strip YAML frontmatter."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3 :]
    return text.strip()


def escape_typst(text: str) -> str:
    """Escape text for Typst content mode and convert simple markdown links."""
    if not text:
        return ""

    links: list[str] = []

    def save_link(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2).replace('"', '\\"')
        label = label.replace("\\", "\\\\")
        label = label.replace("#", "\\#")
        label = label.replace("@", "\\@")
        label = label.replace("$", "\\$")
        label = re.sub(r"\*\*(.+?)\*\*", r"*\1*", label)
        links.append(f'#link("{url}")[{label}]')
        return f"\x00L{len(links) - 1}\x00"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", save_link, text)
    text = text.replace("\\", "\\\\")
    text = text.replace("#", "\\#")
    text = text.replace("@", "\\@")
    text = text.replace("$", "\\$")
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)

    for i, link in enumerate(links):
        text = text.replace(f"\x00L{i}\x00", link)
    return text


def extract_section(text: str, heading: str) -> str:
    """Extract content after a heading until the next heading or rule."""
    escaped = re.escape(heading)
    match = re.search(rf"^{escaped}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    level = len(re.match(r"^#+", heading).group())  # type: ignore[arg-type]
    end_match = re.search(
        rf"^(?:#{{1,{level}}}\s|---\s*$)", text[start:], re.MULTILINE
    )
    if end_match:
        return text[start : start + end_match.start()].strip()
    return text[start:].strip()


def parse_table(text: str) -> list[dict[str, str]]:
    """Parse a markdown table into row dictionaries."""
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return []

    def split_row(line: str) -> list[str]:
        cells = [cell.strip() for cell in line.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        return cells

    headers = split_row(lines[0])
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        cells = split_row(line)
        row = {}
        for i, header in enumerate(headers):
            row[header] = cells[i] if i < len(cells) else ""
        rows.append(row)
    return rows


def parse_bullets(text: str) -> list[str]:
    """Parse unordered or ordered markdown list items."""
    items: list[str] = []
    current: str | None = None
    for line in text.splitlines():
        match = re.match(r"^(?:[-*]|\d+\.)\s+(.+)", line.strip())
        if match:
            if current is not None:
                items.append(current)
            current = match.group(1).strip()
        elif current is not None and line.strip():
            current += " " + line.strip()
    if current is not None:
        items.append(current)
    return items


def find_level3_sections(text: str) -> list[tuple[str, str]]:
    """Split text at level-3 headings."""
    parts = re.split(r"^###\s+", text, flags=re.MULTILINE)
    results: list[tuple[str, str]] = []
    for part in parts[1:]:
        lines = part.split("\n", 1)
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""
        results.append((title, content))
    return results


def resume_items(items: list[str]) -> str:
    """Render bullet items with modern-cv's resume-item component."""
    if not items:
        return ""
    lines = [f"  - {escape_typst(item)}" for item in items]
    return "#resume-item[\n" + "\n".join(lines) + "\n]"


def infer_repo_slug() -> tuple[str, str] | None:
    """Infer the GitHub owner/repo from Actions env or the local git remote."""
    github_repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if "/" in github_repository:
        owner, repo = github_repository.split("/", 1)
        if owner and repo:
            return owner, repo

    try:
        remote = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None

    match = re.search(r"github\.com[:/]([^/]+)/(.+?)(?:\.git)?$", remote)
    if not match:
        return None
    return match.group(1), match.group(2)


def infer_homepage() -> str:
    """Infer a stable homepage URL for the CV header."""
    explicit = os.environ.get("CV_HOMEPAGE", "").strip()
    if explicit:
        return explicit.rstrip("/")

    site_url = os.environ.get("SITE_URL", "").strip()
    if site_url:
        return site_url.rstrip("/")

    slug = infer_repo_slug()
    if slug is not None:
        owner, repo = slug
        return f"https://{owner}.github.io/{repo}"

    return "https://github.com"


def infer_github_user() -> str:
    """Infer the GitHub username shown in the CV header."""
    explicit = os.environ.get("CV_GITHUB", "").strip()
    if explicit:
        return explicit

    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "").strip()
    if owner:
        return owner

    slug = infer_repo_slug()
    if slug is not None:
        owner, _repo = slug
        return owner

    return "SCAU-Algae"


def gen_preamble() -> str:
    """Generate Typst preamble."""
    homepage = infer_homepage()
    github_user = infer_github_user()
    return f"""#import "@preview/modern-cv:0.9.0": *

#fa-version("6")
#show "R茅sum茅": "CV"

#show: resume.with(
  author: (
    firstname: "Li",
    lastname: "Guang",
    email: "841143092@qq.com",
    phone: "(+86) 186-1702-7258",
    homepage: "{homepage}",
    github: "{github_user}",
    address: "Shenzhen, China",
    positions: (
      "Technical Project Management",
      "Spatial Data & AI",
    ),
    custom: (),
  ),
  profile-picture: "pages/images/profile-avatar.png",
  date: datetime.today().display(),
  language: "en",
  paper-size: "us-letter",
  accent-color: default-accent-color,
  colored-headers: true,
  show-footer: true,
)

#set heading(bookmarked: true)
#set document(title: "Li Guang - CV")"""


def gen_profile(about: str) -> str:
    """Generate summary section."""
    content = extract_section(about, "# 个人简介")
    if not content:
        return ""
    return "= 个人简介\n\n" + escape_typst(content)


def gen_targets(about: str) -> str:
    """Generate job target section."""
    rows = parse_table(extract_section(about, "## 求职方向"))
    if not rows:
        return ""
    items = []
    for row in rows:
        items.append(
            " / ".join(
                [
                    row.get("方向", ""),
                    row.get("城市", ""),
                    row.get("薪资预期", ""),
                    row.get("当前定位", ""),
                ]
            )
        )
    return "= 求职方向\n\n" + resume_items(items)


def gen_education(about: str) -> str:
    """Generate education section."""
    rows = parse_table(extract_section(about, "## 教育经历"))
    if not rows:
        return ""
    lines = ["= 教育经历\n"]
    for row in rows:
        lines.append(
            "#resume-entry(\n"
            f'  title: [{escape_typst(row.get("学位 / 专业", ""))}],\n'
            f'  location: [{escape_typst(row.get("学校", ""))}],\n'
            f'  date: [{escape_typst(row.get("时间", ""))}],\n'
            f'  description: [{escape_typst(row.get("说明", ""))}],\n'
            ")"
        )
    return "\n\n".join(lines)


def gen_strengths(about: str) -> str:
    """Generate strengths section."""
    items = parse_bullets(extract_section(about, "## 个人优势"))
    if not items:
        return ""
    return "= 个人优势\n\n" + resume_items(items)


def gen_research(research: str) -> str:
    """Generate research directions section."""
    items = parse_bullets(extract_section(research, "## 研究方向"))
    if not items:
        return ""
    return "= 研究方向\n\n" + resume_items(items)


def gen_methods(research: str) -> str:
    """Generate methods and tools section."""
    items = parse_bullets(extract_section(research, "## 方法与工具"))
    if not items:
        return ""
    return "= 方法与工具\n\n" + resume_items(items)


def gen_publications(research: str) -> str:
    """Generate publication section."""
    items = parse_bullets(extract_section(research, "## 论文发表"))
    if not items:
        return ""
    return "= 论文发表\n\n" + resume_items(items)


def gen_projects(software: str) -> str:
    """Generate project section."""
    content = extract_section(software, "## 重点项目")
    sections = find_level3_sections(content)
    if not sections:
        return ""
    parts = ["= 项目经历\n"]
    for title, body in sections:
        time = (re.search(r"\*\*时间：\*\*\s*(.+)", body) or [None, ""])[1]
        role = (re.search(r"\*\*角色：\*\*\s*(.+)", body) or [None, ""])[1]
        bullets = parse_bullets(body)
        parts.append(f"== {escape_typst(title)}\n")
        meta = []
        if time:
            meta.append(f"时间：{time}")
        if role:
            meta.append(f"角色：{role}")
        if meta:
            parts.append(escape_typst(" | ".join(meta)) + "\n")
        if bullets:
            parts.append(resume_items(bullets))
    return "\n".join(parts).strip()


def gen_internships(services: str) -> str:
    """Generate internship section."""
    sections = find_level3_sections(services)
    if not sections:
        return ""
    parts = ["= 实习经历\n"]
    for title, body in sections:
        time = (re.search(r"\*\*时间：\*\*\s*(.+)", body) or [None, ""])[1]
        role = (re.search(r"\*\*岗位：\*\*\s*(.+)", body) or [None, ""])[1]
        stage_items: list[str] = []
        main_items: list[str] = []
        in_stage = False
        for line in body.splitlines():
            if line.strip().startswith("**阶段成果"):
                in_stage = True
                continue
            if in_stage:
                stage_items.extend(parse_bullets(line))
            else:
                main_items.extend(parse_bullets(line))

        parts.append(f"== {escape_typst(title)}\n")
        meta = []
        if time:
            meta.append(f"时间：{time}")
        if role:
            meta.append(f"岗位：{role}")
        if meta:
            parts.append(escape_typst(" | ".join(meta)) + "\n")
        if main_items:
            parts.append(resume_items(main_items))
        if stage_items:
            parts.append("=== 阶段成果\n")
            parts.append(resume_items(stage_items))
    return "\n".join(parts).strip()


def gen_skills(skills_text: str) -> str:
    """Generate skills section."""
    parts = ["= 专业技能\n"]
    for heading in ["## GIS 与空间数据", "## AI 建模", "## 开发与协作"]:
        title = heading.replace("## ", "")
        items = parse_bullets(extract_section(skills_text, heading))
        if items:
            parts.append(f"== {escape_typst(title)}\n")
            parts.append(resume_items(items))
    return "\n".join(parts).strip()


def gen_awards(awards: str) -> str:
    """Generate awards, certificates, and campus work section."""
    parts = []
    rows = parse_table(extract_section(awards, "## 奖学金与荣誉"))
    if rows:
        items = [f'{row.get("时间", "")}: {row.get("荣誉", "")}' for row in rows]
        parts.append("= 荣誉与证书\n")
        parts.append("== 奖学金与荣誉\n")
        parts.append(resume_items(items))

    certs = parse_bullets(extract_section(awards, "## 资格证书"))
    if certs:
        parts.append("== 资格证书\n")
        parts.append(resume_items(certs))

    campus = parse_bullets(extract_section(awards, "## 校园经历"))
    if campus:
        parts.append("== 校园经历\n")
        parts.append(resume_items(campus))

    return "\n".join(parts).strip()


def gen_reports(talks: str) -> str:
    """Generate communication and writing section."""
    parts = ["= 汇报与写作\n"]
    for heading in ["## 主要输出", "## 相关经验"]:
        title = heading.replace("## ", "")
        items = parse_bullets(extract_section(talks, heading))
        if items:
            parts.append(f"== {escape_typst(title)}\n")
            parts.append(resume_items(items))
    return "\n".join(parts).strip()


def main() -> None:
    """Read page content and generate cv.typ."""
    root = Path(__file__).parent
    pages = root / "pages"

    about = read_file(pages / "about.md")
    research = read_file(pages / "research.md")
    software = read_file(pages / "software.md")
    services = read_file(pages / "services.md")
    skills_text = read_file(pages / "teaching.md")
    awards = read_file(pages / "awards.md")
    talks = read_file(pages / "talks.md")

    sections = [
        gen_preamble(),
        gen_profile(about),
        gen_targets(about),
        gen_education(about),
        gen_strengths(about),
        gen_research(research),
        gen_methods(research),
        gen_publications(research),
        gen_projects(software),
        gen_internships(services),
        gen_skills(skills_text),
        gen_awards(awards),
        gen_reports(talks),
    ]

    output = "\n\n".join(section for section in sections if section)
    out_path = root / "cv.typ"
    out_path.write_text(output, encoding="utf-8")
    print(f"Generated {out_path} ({len(output):,} bytes)")


if __name__ == "__main__":
    main()
