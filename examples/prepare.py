"""Local teaching example. No network, model, browser, or publication action."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path


def inspect_manifest(path: Path) -> tuple[dict, list[dict], list[str]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("清单必须是 JSON 对象")
    errors: list[str] = []
    if not re.fullmatch(r"K\.\d{4}", str(data.get("public_number", ""))):
        errors.append("教学编号需为 K.0001 形式")
    for key in ("title", "body"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{key} 必须为非空文字")
    tags = data.get("tags")
    if (not isinstance(tags, list) or not 1 <= len(tags) <= 10
            or not all(isinstance(t, str) and t.strip() and not re.search(r"[\s#]", t) for t in tags)
            or len(set(tags)) != len(tags)):
        errors.append("tags 必须有 1 至 10 个不重复且不含空格、# 的标签")
    stamp = data.get("publish_at", "")
    if not isinstance(stamp, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}", stamp):
        errors.append("publish_at 必须是含秒和时区的完整日期时间")
    else:
        try:
            datetime.fromisoformat(stamp)
        except ValueError:
            errors.append("publish_at 日期或时间无效")
    review = data.get("review")
    for key in ("topic_and_facts_verified", "visual_content_verified", "cover_identity_verified"):
        if not isinstance(review, dict) or review.get(key) is not True:
            errors.append(f"缺少真实人工检查记录：{key}")
    roles = data.get("expected_roles")
    if (not isinstance(roles, list) or not roles
            or not all(isinstance(x, str) and re.fullmatch(r"[a-z][a-z0-9_]*", x) for x in roles)
            or len(set(roles)) != len(roles)):
        errors.append("expected_roles 需要有序且唯一的页面角色")
    media = data.get("media")
    files: list[dict] = []
    if not isinstance(media, list) or not all(isinstance(x, dict) for x in media):
        errors.append("media 必须是素材清单")
        media = []
    if [x.get("role") for x in media] != roles:
        errors.append("素材数量、角色或顺序与 expected_roles 不一致")
    base = path.parent.resolve()
    used_paths: set[Path] = set()
    for entry in media:
        value = entry.get("path")
        if not isinstance(value, str) or not value or Path(value).is_absolute():
            errors.append("素材路径必须是相对路径")
            continue
        source = (base / value).resolve()
        if not source.is_relative_to(base) or not source.is_file():
            errors.append(f"素材不存在或超出清单目录：{value}")
            continue
        if source in used_paths:
            errors.append(f"同一素材不能重复充当不同页面：{value}")
            continue
        used_paths.add(source)
        raw = source.read_bytes()
        suffix = source.suffix.lower()
        valid = ((suffix == ".png" and raw.startswith(b"\x89PNG\r\n\x1a\n"))
                 or (suffix in {".jpg", ".jpeg"} and raw.startswith(b"\xff\xd8\xff"))
                 or (suffix == ".webp" and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"))
        if not valid:
            errors.append(f"图片扩展名或文件头无效：{value}")
            continue
        files.append({"role": entry.get("role"), "source": source,
                      "relative_source": value, "sha256": hashlib.sha256(raw).hexdigest()})
    return data, files, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, help="新目录；省略时只检查")
    args = parser.parse_args()
    try:
        data, files, errors = inspect_manifest(args.manifest.resolve())
        if errors:
            print(json.dumps({"ok": False, "errors": errors, "submitted": False}, ensure_ascii=False, indent=2))
            return 2
        if args.out:
            output = args.out.resolve()
            if output.exists():
                raise ValueError("输出目录已存在，拒绝覆盖")
            output.mkdir(parents=True, exist_ok=False)
            (output / "images").mkdir()
            media = []
            for index, entry in enumerate(files, 1):
                target = Path("images") / f"{index:02d}_{entry['role']}{entry['source'].suffix.lower()}"
                shutil.copyfile(entry["source"], output / target)
                if hashlib.sha256((output / target).read_bytes()).hexdigest() != entry["sha256"]:
                    raise ValueError("复制后素材哈希不一致，当前目录需人工检查")
                media.append({"role": entry["role"], "path": target.as_posix(),
                              "source": entry["relative_source"], "sha256": entry["sha256"]})
            text = f"【标题】\n{data['title'].strip()}\n\n【正文】\n{data['body'].strip()}\n\n"
            text += " ".join("#" + t for t in data["tags"]) + "\n"
            (output / "发布包.txt").write_text(text, encoding="utf-8")
            result = {"public_number": data["public_number"], "publish_at": data["publish_at"],
                      "production_status": "PACKAGE_READY", "review_status": "PENDING_FINAL_HUMAN_REVIEW",
                      "platform_status": "NOT_SUBMITTED", "submitted": False, "media": media}
            (output / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "operation": "prepared" if args.out else "checked",
                          "media_count": len(files), "submitted": False}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"ok": False, "error": str(error), "submitted": False}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
