"""
post_to_linkedin.py
----------------------
LinkedIn ke official UGC Posts API se text-post publish karta hai.

ZAROORI environment variables (README.md mein poora process hai):
    LINKEDIN_ACCESS_TOKEN   -> LinkedIn Developer Portal se milega
    LINKEDIN_PERSON_URN     -> tumhare profile ka unique ID
                               (format: urn:li:person:XXXXXXXXXX)

Is file mein kahin bhi apni key/token type NAHI karni - sab kuch
GitHub Secrets se apne aap aata hai.
"""

import os
import requests

LINKEDIN_API_URL = "https://api.linkedin.com/v2/ugcPosts"


def post_to_linkedin(post_text):
    """
    post_text: wo final text jo LinkedIn par publish karna hai
    Return: True (success) ya Exception raise karega (failure)
    """
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
    }

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
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
    # Standalone test ke liye: python scripts/post_to_linkedin.py
    # DHYAN RAKHNA: ye turant real post karega tumhare LinkedIn par!
    test_text = "This is a test post from my automation system. #Testing"
    post_to_linkedin(test_text)
    print("Post successful!")
