"""
post_to_linkedin.py
----------------------
LinkedIn ke naye "Posts API" se text-post publish karta hai.
(Purana /v2/ugcPosts endpoint 2023 mein retire ho chuka hai naye apps ke liye,
isliye naya /rest/posts endpoint use kar rahe hain.)
"""

import os
import requests

LINKEDIN_API_URL = "https://api.linkedin.com/rest/posts"
LINKEDIN_API_VERSION = "202608"   # YYYYMM format


def post_to_linkedin(post_text):
    access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.environ.get("LINKEDIN_PERSON_URN")

    if not access_token:
        raise EnvironmentError("LINKEDIN_ACCESS_TOKEN set nahi hai.")
    if not person_urn:
        raise EnvironmentError("LINKEDIN_PERSON_URN set nahi hai.")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": LINKEDIN_API_VERSION,
    }

    payload = {
        "author": person_urn,
        "commentary": post_text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    response = requests.post(
        LINKEDIN_API_URL, headers=headers, json=payload, timeout=30
    )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"LinkedIn post fail hua. Status: {response.status_code}, "
            f"Response: {response.text}"
        )

    return True


if __name__ == "__main__":
    test_text = "This is a test post from my automation system. #Testing"
    post_to_linkedin(test_text)
    print("Post successful!")
