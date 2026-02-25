# React Query Setup - Task 4.7 Complete

## Summary

Successfully set up React Query (`@tanstack/react-query`) for API calls in the Hedera Flow MVP application. The implementation provides a robust, type-safe data fetching and caching layer for all API interactions.

## What Was Implemented

### 1. Core Configuration Files

#### `lib/queryClient.ts`
- Configured global QueryClient with optimized defaults
- 5-minute stale time for data freshness
- 10-minute cache time for performance
- Automatic retry logic for failed requests

#### `lib/api.ts`
- Axios-based API client with base URL configuration
- JWT token injection via request interceptor
- Automatic 401 handling (logout on unauthorized)
- Error handling utilities (`getErrorMessage`)
- Type-safe request wrapper

#### `components/Providers.tsx`
- Client component wrapper for QueryClientProvider
- React Query Devtools integration (development only)
- Compatible with Next.js 14 App Router

### 2. API Hooks (Custom React Query Hooks)

Created comprehensive hooks for all API endpoints:

#### Authentication (`hooks/useAuth.ts`)
- `useUser()` - Fetch current user data
- `useLogin()` - Login mutation
- `useRegister()` - Registration mutation
- `useWalletConnect()` - HashPack wallet connection
- `useLogout()` - Logout with cache clearing

#### Meters (`hooks/useMeters.ts`)
- `useMeters()` - Fetch all user meters
- `useMeter(meterId)` - Fetch single meter
- `useCreateMeter()` - Create new meter
- `useDeleteMeter()` - Delete meter

#### Verifications (`hooks/useVerification.ts`)
- `useVerifications(params)` - Fetch verifications list with filters
- `useVerification(id)` - Fetch single verification
- `useVerifyMeter()` - Submit meter photo for verification (multipart/form-data)

#### Bills (`hooks/useBills.ts`)
- `useBills(params)` - Fetch bills list with filters
- `useBill(billId)` - Fetch single bill

#### Payments (`hooks/usePayments.ts`)
- `usePreparePayment(billId)` - Prepare HBAR payment
- `useConfirmPayment()` - Confirm payment after Hedera transaction

#### Disputes (`hooks/useDisputes.ts`)
- `useDisputes(params)` - Fetch disputes list
- `useDispute(id)` - Fetch single dispute
- `useCreateDispute()` - Create dispute with evidence upload

#### Exchange Rates (`hooks/useExchangeRate.ts`)
- `useExchangeRate(currency)` - Fetch HBAR exchange rate (auto-refetch every 5 min)
- `useFiatToHbar(amount, currency)` - Helper to convert fiat to HBAR

### 3. Integration with Next.js

Updated `app/layout.tsx` to wrap the application with the Providers component, enabling React Query throughout the app.

### 4. Documentation

Created comprehensive `lib/README.md` with:
- Usage examples for queries and mutations
- File upload examples
- Best practices for query keys and invalidation
- Testing guidelines
- Environment variable configuration

## Key Features

### Type Safety
All hooks are fully typed with TypeScript interfaces for:
- Request payloads
- Response data
- Error handling

### Automatic Cache Management
- Queries are cached and automatically revalidated
- Mutations invalidate related queries
- Optimistic updates supported

### Error Handling
- Centralized error handling in API client
- User-friendly error messages
- Automatic token refresh on 401

### File Uploads
- Support for multipart/form-data (meter photos, dispute evidence)
- Progress tracking capability

### Real-time Data
- Exchange rates auto-refetch every 5 minutes
- Configurable refetch intervals per query

## Environment Variables

Add to `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Usage Example

```typescript
import { useMeters, useCreateMeter } from '@/hooks/useMeters';

function MeterManagement() {
  const { data: meters, isLoading } = useMeters();
  const createMeter = useCreateMeter();

  const handleCreate = async (data) => {
    await createMeter.mutateAsync(data);
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h1>My Meters</h1>
      <ul>
        {meters?.map(meter => (
          <li key={meter.id}>{meter.meterId}</li>
        ))}
      </ul>
      <button onClick={() => handleCreate({ /* data */ })}>
        Add Meter
      </button>
    </div>
  );
}
```

## React Query Devtools

In development mode, open the devtools by clicking the React Query icon in the bottom-left corner to:
- Inspect active queries
- View cache data
- Debug query states
- Monitor mutations

## Testing

All TypeScript compilation passes with no errors:
```bash
npx tsc --noEmit
# ✓ No errors
```

## Next Steps

The React Query setup is complete and ready for use. Backend developers can now:

1. Implement the FastAPI endpoints that match the API specifications
2. Frontend developers can use the hooks immediately (they'll work once backend is ready)
3. Add more hooks as new endpoints are created

## Files Created

```
lib/
├── queryClient.ts          # React Query client configuration
├── api.ts                  # Axios API client with interceptors
└── README.md               # Comprehensive documentation

components/
└── Providers.tsx           # QueryClientProvider wrapper

hooks/
├── useAuth.ts              # Authentication hooks
├── useMeters.ts            # Meter management hooks
├── useVerification.ts      # Verification hooks
├── useBills.ts             # Bill hooks
├── usePayments.ts          # Payment hooks
├── useDisputes.ts          # Dispute hooks
└── useExchangeRate.ts      # Exchange rate hooks

app/
└── layout.tsx              # Updated with Providers wrapper
```

## Dependencies Installed

- `@tanstack/react-query` (already installed)
- `@tanstack/react-query-devtools` (newly installed)

## Task Status

✅ Task 4.7 - Set up React Query for API calls - **COMPLETE**

All requirements met:
- React Query configured with optimal defaults
- API client with JWT authentication
- Comprehensive hooks for all endpoints
- Type-safe implementation
- Documentation and examples
- Integration with Next.js 14 App Router
- Development tools (React Query Devtools)
