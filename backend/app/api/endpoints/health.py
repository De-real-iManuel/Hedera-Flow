"""
Health Check Endpoints
System health and status monitoring
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from config import settings
from app.core.rate_limit import limiter
from app.core.database import check_db_connection, get_db_stats, get_db

router = APIRouter()


@router.get("/health")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def health_check(request: Request):
    """
    Comprehensive health check endpoint
    Returns status of all system components
    
    Rate limited to prevent abuse
    """
    # Check database connection
    db_healthy = check_db_connection()
    db_status = "operational" if db_healthy else "unavailable"
    
    # Get database pool stats if healthy
    db_stats = None
    if db_healthy:
        try:
            db_stats = get_db_stats()
        except Exception:
            db_stats = None
    
    return JSONResponse({
        "status": "healthy" if db_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "version": "1.0.0",
        "components": {
            "api": "operational",
            "database": db_status,
            "redis": "not_configured",      # TODO: Check Redis connection
            "hedera": "not_configured"      # TODO: Check Hedera network
        },
        "database_pool": db_stats
    })


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness probe for Kubernetes/container orchestration
    Returns 200 if service is ready to accept traffic
    """
    # Check if database is ready
    db_ready = check_db_connection()
    
    if not db_ready:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "Database not ready"}
        )
    
    return {"ready": True}


@router.get("/health/live")
async def liveness_check():
    """
    Liveness probe for Kubernetes/container orchestration
    Returns 200 if service is alive
    """
    return {"alive": True}


@router.post("/health/fix-schema")
async def fix_schema():
    """
    Emergency endpoint: add missing columns to users table.
    Safe to call multiple times (uses IF NOT EXISTS).
    Call this immediately after deploy if Railway logs show UndefinedColumn errors.
    """
    from sqlalchemy import text
    from app.core.database import engine

    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS evm_address VARCHAR(42)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS kms_key_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_expires TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subsidy_eligible BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subsidy_type VARCHAR(50)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subsidy_verified_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subsidy_expires_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS security_settings JSONB",
        # Widen hedera_tx_id to hold full canonical tx IDs (e.g. 0.0.7942971@1234567890.000000000)
        "ALTER TABLE prepaid_tokens ALTER COLUMN hedera_tx_id TYPE VARCHAR(255)",
    ]

    results = []
    errors = []
    with engine.connect() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                conn.commit()
                results.append(f"OK: {stmt}")
            except Exception as e:
                errors.append(f"ERR ({stmt}): {str(e)}")

    # Verify columns exist
    with engine.connect() as conn:
        cols = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY column_name"
        )).fetchall()
    column_names = [r[0] for r in cols]

    return {
        "applied": results,
        "errors": errors,
        "users_columns": column_names,
        "evm_address_exists": "evm_address" in column_names,
        "kms_key_id_exists": "kms_key_id" in column_names,
    }


@router.post("/health/seed-tariffs")
async def seed_tariffs(db: Session = Depends(get_db)):
    """Force-seed tariffs and return current DB state"""
    NG_BANDS = '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}'
    ROWS = [
        ('NG','Eko Electricity Distribution Company',   'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Ikeja Electric',                         'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Abuja Electricity Distribution Company', 'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Enugu Electricity Distribution Company', 'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Port Harcourt Electricity Distribution', 'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Port Harcourt Electricity Distribution Company', 'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Ibadan Electricity Distribution Company','NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Kano Electricity Distribution Company',  'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Kaduna Electricity Distribution Company','NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Jos Electricity Distribution Company',   'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Benin Electricity Distribution Company', 'NGN', NG_BANDS, '{"vat":0.075}'),
        ('NG','Yola Electricity Distribution Company',  'NGN', NG_BANDS, '{"vat":0.075}'),
        ('ES','Iberdrola','EUR','{"type":"flat","rate":0.18}','{"vat":0.21}'),
        ('ES','Endesa',   'EUR','{"type":"flat","rate":0.18}','{"vat":0.21}'),
        ('ES','Naturgy',  'EUR','{"type":"flat","rate":0.18}','{"vat":0.21}'),
        ('US','Pacific Gas & Electric','USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('US','Con Edison',            'USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('US','ComEd',                 'USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('US','Florida Power & Light', 'USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('US','Texas Electric',        'USD','{"type":"tiered","tiers":[{"limit":500,"price":0.12},{"limit":null,"price":0.18}]}','{"tax":0.08}'),
        ('IN','Tata Power',   'INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('IN','BSES Rajdhani','INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('IN','BSES Yamuna',  'INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('IN','BESCOM',       'INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('IN','TNEB',         'INR','{"type":"tiered","tiers":[{"limit":100,"price":3.5},{"limit":300,"price":5.5},{"limit":null,"price":7.5}]}','{"tax":0.05}'),
        ('BR','CEMIG',         'BRL','{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}','{"icms":0.20}'),
        ('BR','ENEL São Paulo','BRL','{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}','{"icms":0.20}'),
        ('BR','COPEL',         'BRL','{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}','{"icms":0.20}'),
        ('BR','CELPE',         'BRL','{"type":"tiered","tiers":[{"limit":200,"price":0.65},{"limit":null,"price":0.85}]}','{"icms":0.20}'),
    ]

    import json as _json

    NG_BANDS_JSON = '{"type":"band_based","bands":[{"name":"A","hours_min":20,"price":225},{"name":"B","hours_min":16,"price":63},{"name":"C","hours_min":12,"price":50},{"name":"D","hours_min":8,"price":43},{"name":"E","hours_min":0,"price":40}]}'

    # Fix any existing NG tariffs that use "band" key instead of "name" key
    try:
        db.execute(text(
            "UPDATE tariffs SET rate_structure = cast(:rs AS jsonb) "
            "WHERE country_code='NG' AND is_active=true "
            "AND rate_structure::text LIKE '%\"band\"%'"
        ), {"rs": NG_BANDS_JSON})
        db.commit()
    except Exception as e:
        db.rollback()

    # Remove any bad/stub rows that don't match canonical provider names
    canonical = {r[1] for r in ROWS}
    placeholders = ", ".join(f":p{i}" for i in range(len(canonical)))
    params_del = {f"p{i}": v for i, v in enumerate(canonical)}
    db.execute(text(f"DELETE FROM tariffs WHERE utility_provider NOT IN ({placeholders})"), params_del)
    db.commit()

    inserted = []
    errors = []
    for (cc, provider, currency, rate_json, taxes_json) in ROWS:
        try:
            # Check existence first
            exists = db.execute(text(
                "SELECT 1 FROM tariffs WHERE country_code=:cc AND utility_provider=:p AND is_active=true"
            ), {"cc": cc, "p": provider}).fetchone()
            if exists:
                continue
            # Use cast() in SQL to avoid psycopg2 named-param + :: conflict
            db.execute(text(
                "INSERT INTO tariffs (country_code, utility_provider, currency, rate_structure, taxes_and_fees, valid_from, is_active) "
                "VALUES (:cc, :provider, :currency, cast(:rate AS jsonb), cast(:taxes AS jsonb), '2024-01-01', true)"
            ), {"cc": cc, "provider": provider, "currency": currency, "rate": rate_json, "taxes": taxes_json})
            db.commit()
            inserted.append(f"{cc}/{provider}")
        except Exception as e:
            db.rollback()
            errors.append(f"{cc}/{provider}: {str(e)}")

    all_tariffs = db.execute(text(
        "SELECT country_code, utility_provider FROM tariffs WHERE is_active=true ORDER BY country_code, utility_provider"
    )).fetchall()

    return {
        "inserted": inserted,
        "errors": errors,
        "total_active_tariffs": len(all_tariffs),
        "tariffs": [{"country": r[0], "provider": r[1]} for r in all_tariffs]
    }


@router.get("/health/hedera-diag")
async def hedera_diagnostics():
    """
    Diagnose Hedera SDK + JVM availability on the running container.
    Call this to see exactly what's failing before pay-custodial.
    """
    import subprocess, shutil, os, sys

    result = {
        "java_home": os.environ.get("JAVA_HOME"),
        "path": os.environ.get("PATH"),
        "java_which": shutil.which("java"),
        "javac_which": shutil.which("javac"),
        "java_version": None,
        "hedera_sdk_importable": False,
        "hedera_client_init": False,
        "operator_id_set": bool(getattr(settings, "hedera_operator_id", None)),
        "operator_key_set": bool(getattr(settings, "hedera_operator_key", None)),
        "error": None,
    }

    # Try java -version
    try:
        out = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=10)
        result["java_version"] = out.stderr.strip() or out.stdout.strip()
    except Exception as e:
        result["java_version"] = f"ERROR: {e}"

    # Try importing hedera SDK
    try:
        from hedera import Client
        result["hedera_sdk_importable"] = True
    except Exception as e:
        result["error"] = f"hedera import failed: {e}"
        return result

    # Try creating a client
    try:
        from hedera import Client, AccountId, PrivateKey
        client = Client.forTestnet()
        op_id = getattr(settings, "hedera_operator_id", None)
        op_key = getattr(settings, "hedera_operator_key", None)
        if op_id and op_key:
            client.setOperator(AccountId.fromString(op_id), PrivateKey.fromString(op_key))
        client.close()
        result["hedera_client_init"] = True
    except Exception as e:
        result["error"] = f"client init failed: {e}"

    return result


@router.post("/health/backfill-hedera-accounts")
async def backfill_hedera_accounts(db: Session = Depends(get_db)):
    """
    Attempt to create real Hedera accounts for users that registered before
    custodial wallet implementation (hedera_account_id IS NULL or starts with 0.0.PENDING_).
    
    Requires HEDERA_OPERATOR_ID and HEDERA_OPERATOR_KEY to be set on Railway.
    Safe to call multiple times — skips users that already have real accounts.
    """
    from sqlalchemy import text as _text
    from app.services.hedera_service import get_hedera_service

    # Find users needing real accounts
    rows = db.execute(_text("""
        SELECT id, email FROM users
        WHERE hedera_account_id IS NULL
           OR hedera_account_id LIKE '0.0.PENDING_%'
        ORDER BY created_at ASC
    """)).fetchall()

    if not rows:
        return {"message": "No users need backfill", "processed": 0}

    hedera_svc = get_hedera_service()
    results = {"success": [], "failed": [], "total_pending": len(rows)}

    for user_id, email in rows:
        try:
            account_id, private_key_str = hedera_svc.create_account(initial_balance_hbar=10.0)

            # Store KMS-encrypted key if AWS KMS is configured
            kms_key_id = None
            encrypted_pk_b64 = None
            try:
                from app.services.aws_kms_service import get_kms_service
                kms = get_kms_service()
                if kms.is_available:
                    context_label = f"user-{email}"
                    encrypted_pk_b64 = kms.store_private_key(private_key_str, context_label)
                    kms_key_id = kms.master_key_id
                    logger.info(f"✅ KMS key stored for backfill user {email}")
                else:
                    logger.warning(f"KMS unavailable for backfill user {email}")
            except Exception as kms_err:
                logger.warning(f"KMS storage failed for {email}: {kms_err}")

            db.execute(_text("""
                UPDATE users
                SET hedera_account_id = :account_id,
                    kms_key_id = :kms_key_id,
                    wallet_type = 'system_generated',
                    preferences = jsonb_set(
                        COALESCE(preferences, '{}'),
                        '{encrypted_hedera_key}',
                        to_jsonb(:encrypted_pk::text)
                    )
                WHERE id = :user_id
            """), {
                "account_id": account_id,
                "kms_key_id": kms_key_id,
                "encrypted_pk": encrypted_pk_b64,
                "user_id": str(user_id)
            })
            db.commit()

            results["success"].append({"email": email, "account_id": account_id})
            logger.info(f"✅ Backfilled Hedera account {account_id} for {email}")

        except Exception as e:
            db.rollback()
            results["failed"].append({"email": email, "error": str(e)})
            logger.error(f"Backfill failed for {email}: {e}")

    return results


@router.post("/health/refresh-custodial-wallet")
async def refresh_custodial_wallet(
    db: Session = Depends(get_db),
):
    """
    Re-generate custodial Hedera wallets for ALL users who have a real account
    but no KMS-encrypted private key stored (registered before KMS was configured).

    This creates a NEW Hedera account for each such user (funded with 10 HBAR from
    operator) and stores the private key in AWS KMS. The old account is replaced.

    Safe to call multiple times — skips users that already have a KMS key.
    """
    from sqlalchemy import text as _text
    from app.services.hedera_service import get_hedera_service
    from app.services.aws_kms_service import get_kms_service

    kms = get_kms_service()
    if not kms.is_available:
        return {"error": "AWS KMS not available — set AWS_KMS_MASTER_KEY_ID on Railway"}

    # Find users with a real account but no encrypted key
    rows = db.execute(_text("""
        SELECT id, email, hedera_account_id
        FROM users
        WHERE wallet_type = 'system_generated'
          AND (
            preferences IS NULL
            OR preferences->>'encrypted_hedera_key' IS NULL
            OR preferences->>'encrypted_hedera_key' = 'null'
          )
        ORDER BY created_at ASC
    """)).fetchall()

    if not rows:
        return {"message": "All custodial users already have KMS keys", "processed": 0}

    hedera_svc = get_hedera_service()
    results = {"success": [], "failed": [], "total_needing_refresh": len(rows)}

    for user_id, email, old_account_id in rows:
        try:
            # Create a fresh Hedera account (new key pair, funded by operator)
            new_account_id, private_key_str = hedera_svc.create_account(initial_balance_hbar=10.0)

            # Store in KMS
            context_label = f"user-{email}"
            encrypted_pk_b64 = kms.store_private_key(private_key_str, context_label)

            db.execute(_text("""
                UPDATE users
                SET hedera_account_id = :account_id,
                    kms_key_id = :kms_key_id,
                    preferences = jsonb_set(
                        COALESCE(preferences, '{}'),
                        '{encrypted_hedera_key}',
                        to_jsonb(:encrypted_pk::text)
                    )
                WHERE id = :user_id
            """), {
                "account_id": new_account_id,
                "kms_key_id": kms.master_key_id,
                "encrypted_pk": encrypted_pk_b64,
                "user_id": str(user_id),
            })
            db.commit()

            results["success"].append({
                "email": email,
                "old_account": old_account_id,
                "new_account": new_account_id,
            })
        except Exception as exc:
            db.rollback()
            results["failed"].append({"email": email, "error": str(exc)})

    return results
