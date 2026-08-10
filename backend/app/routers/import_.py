"""Excel 导入路由：preview（Dry-Run）/ commit（事务写入）。"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.models import User
from app.schemas import ImportCommitResp, ImportPreviewResp, ImportRowError, Resp
from app.importer import apply_rows, extract_rows, validate_rows
from app.security import require_user

router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/preview", response_model=Resp)
async def preview(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        raw = extract_rows(content)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Excel 解析失败：{e}")
    if not raw:
        raise HTTPException(status_code=400, detail="文件中未读取到任何数据行（请检查表头与数据）")
    valid, errors = validate_rows(db, raw)
    to_insert = sum(1 for v in valid if v.action == "insert")
    to_update = sum(1 for v in valid if v.action == "update")
    preview_devices = [
        {
            "row": v.row,
            "action": v.action,
            "resource_code": v.data["resource_code"],
            "device_type": v.data["device_type"],
            "brand_name": v.data.get("brand_name", ""),
            "model": v.data.get("model", ""),
            "rack_code": v.data["rack_code"],
            "rack_name": v.data.get("rack_name", ""),
            "start_u": v.data["start_u"],
            "height_u": v.data["height_u"],
            "asset_status": v.data.get("asset_status", "运行中"),
        }
        for v in valid
    ]
    resp = ImportPreviewResp(
        total=len(raw),
        to_insert=to_insert,
        to_update=to_update,
        errors=[ImportRowError(**e) for e in errors],
        preview_devices=preview_devices,
    )
    return Resp(data=resp.model_dump())


@router.post("/commit", response_model=Resp)
async def commit(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(require_user)):
    content = await file.read()
    filename = file.filename or "unknown.xlsx"
    try:
        raw = extract_rows(content)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Excel 解析失败：{e}")

    valid, errors = validate_rows(db, raw)
    total = len(raw)
    failed = len(errors)

    if failed > 0:
        # 整批回滚：不写入任何数据
        log = crud.create_import_log(
            db,
            {
                "filename": filename,
                "total_rows": total,
                "success_count": 0,
                "failed_count": failed,
                "status": "失败",
                "error_detail": json.dumps(errors, ensure_ascii=False),
            },
        )
        db.commit()
        return Resp(
            code=1,
            data=ImportCommitResp(
                total_rows=total,
                success_count=0,
                failed_count=failed,
                import_id=log.id,
                errors=[ImportRowError(**e) for e in errors],
            ).model_dump(),
            msg="导入失败：存在校验错误，已回滚",
        )

    # 全部通过 → 事务写入
    try:
        apply_rows(db, valid, operator=user)
        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        log = crud.create_import_log(
            db,
            {
                "filename": filename,
                "total_rows": total,
                "success_count": 0,
                "failed_count": total,
                "status": "失败",
                "error_detail": json.dumps([{"row": 0, "reason": f"写入异常：{e}"}], ensure_ascii=False),
            },
        )
        db.commit()
        raise HTTPException(status_code=500, detail=f"导入写入失败：{e}")

    log = crud.create_import_log(
        db,
        {
            "filename": filename,
            "total_rows": total,
            "success_count": total,
            "failed_count": 0,
            "status": "成功",
            "error_detail": "{}",
        },
    )
    db.commit()
    return Resp(
        data=ImportCommitResp(
            total_rows=total,
            success_count=total,
            failed_count=0,
            import_id=log.id,
            errors=[],
        ).model_dump(),
        msg=f"导入成功：新增 {sum(1 for v in valid if v.action=='insert')} 条，更新 {sum(1 for v in valid if v.action=='update')} 条",
    )
