import httpx
import asyncio

async def test_backend():
    async with httpx.AsyncClient() as client:
        print("Testing /health...")
        try:
            res = await client.get("http://127.0.0.1:8000/health")
            print(f"Health status: {res.status_code}")
            print(res.json())
        except Exception as e:
            print(f"Health failed: {e}")
            return
            
        print("\nTesting /token...")
        try:
            res = await client.post(
                "http://127.0.0.1:8000/token",
                data={"username": "testuser", "password": "password"}
            )
            print(f"Token status: {res.status_code}")
            token_data = res.json()
            print(token_data)
            token = token_data.get("access_token")
        except Exception as e:
            print(f"Token failed: {e}")
            return
            
        print("\nTesting /api/v1/recruitment/evaluate with invalid token...")
        try:
            # We must use multipart/form-data for the file upload
            res = await client.post(
                "http://127.0.0.1:8000/api/v1/recruitment/evaluate",
                headers={"Authorization": "Bearer invalid_token"},
                data={"job_id": "job123"}
            )
            print(f"Evaluate invalid auth status: {res.status_code}")
        except Exception as e:
            print(f"Evaluate invalid failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_backend())
