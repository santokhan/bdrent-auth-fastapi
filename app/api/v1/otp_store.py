import random
import time
import redis


class OTPStore:
    def __init__(self, redis_host="redis", redis_port=6379):
        self.client = redis.StrictRedis(
            host=redis_host, port=redis_port, db=0, decode_responses=True
        )

    def create(self, phone_number: str) -> str:
        """
        Generates and stores an OTP for the given phone number in Redis.

        :param phone_number: The phone number to associate the OTP with.
        :return: The generated OTP.
        """
        otp = str(random.randint(100000, 999999))  # Generate a 6-digit OTP
        timestamp = time.time()  # Store the current timestamp

        # Save the OTP and timestamp in Redis with a 5-minute expiry (300 seconds)
        self.client.hmset(phone_number, {"otp": otp, "timestamp": timestamp})
        self.client.expire(phone_number, 300)  # Set expiry time for 5 minutes
        return otp

    def read(self, phone_number: str) -> dict:
        """
        Retrieves the OTP and its metadata for the given phone number from Redis.

        :param phone_number: The phone number to retrieve the OTP for.
        :return: A dictionary with OTP and timestamp, or None if not found.
        """
        data = self.client.hgetall(phone_number)
        return data if data else None

    def verify(self, phone_number: str, otp_input=str):
        """
        Matches the input OTP with the stored OTP for the given phone number.

        :param phone_number: The phone number to match the OTP for.
        :param otp_input: The OTP input to verify.
        :return: True if the OTPs match, False otherwise.
        """
        data = self.read(phone_number=phone_number)
        otp_db = data.get("otp", None)

        return otp_db == otp_input

    def is_expired(self, phone_number: str, expiry_time: int = 300) -> bool:
        """
        Checks if the OTP for a given phone number is expired.

        :param phone_number: The phone number to check the OTP for.
        :param expiry_time: The expiry time in seconds (default: 300 seconds).
        :return: True if the OTP is expired, False otherwise.
        """
        data = self.read(phone_number)
        if not data:
            return True

        timestamp = float(data["timestamp"])
        return time.time() - timestamp > expiry_time

    def delete(self, phone_number: str) -> bool:
        """
        Deletes the OTP associated with the given phone number from Redis.

        :param phone_number: The phone number to delete the OTP for.
        :return: True if the OTP was deleted, False otherwise.
        """
        return self.client.delete(phone_number) > 0


if __name__ == "__main__":
    import asyncio

    store = OTPStore()

    # Test 1: Create OTP and read immediately
    store.create(phone_number="01307230077")
    print("Initial OTP data (Test 1):", store.read(phone_number="01307230077"))

    # Test 2: Create OTP for another phone number and read immediately
    store.create(phone_number="01718787756")
    print("Initial OTP data (Test 2):", store.read(phone_number="01718787756"))

    # Wait for 5 minutes
    async def wait_and_test():
        print("Waiting for seconds...")
        await asyncio.sleep(10)  # 300 seconds = 5 minutes

        # Test expiration for the first phone number
        expired_1 = store.is_expired(phone_number="01307230077", expiry_time=5)
        print("Is OTP expired (Test 1):", expired_1)

        # Test expiration for the second phone number
        expired_2 = store.is_expired(phone_number="01718787756", expiry_time=15)
        print("Is OTP expired (Test 2):", expired_2)

    asyncio.run(wait_and_test())
