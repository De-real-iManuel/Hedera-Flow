"""
Quick test to verify token creation uses 'pending' status
"""
import sys
sys.path.insert(0, '.')

from app.services.prepaid_token_service import PrepaidTokenService
from app.core.database import SessionLocal

def test_token_creation_status():
    """Test that tokens are created with pending status"""
    db = SessionLocal()
    
    try:
        service = PrepaidTokenService(db)
        
        # Create a test token
        token_data = service.create_token(
            user_id="790b78b0-aca4-45a3-8b34-2d9261870c5a",
            meter_id="029e73b0-9235-45aa-bdf3-900eabe87b76",
            amount_fiat=10.0,
            currency="NGN",
            country_code="NG",
            utility_provider="Port Harcourt Electricity Distribution Company",
            payment_method="HBAR"
        )
        
        print(f"✅ Token created: {token_data['token_id']}")
        print(f"   Status: {token_data['status']}")
        print(f"   Amount HBAR: {token_data.get('amount_paid_hbar')}")
        print(f"   Units: {token_data['units_purchased']} kWh")
        
        if token_data['status'] == 'pending':
            print("\n✅ SUCCESS! Token created with 'pending' status")
            return True
        else:
            print(f"\n❌ FAILED! Token created with '{token_data['status']}' status (expected 'pending')")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_token_creation_status()
    sys.exit(0 if success else 1)
