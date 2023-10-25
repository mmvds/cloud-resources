import requests
# 243438 243520
url = "https://codenrock.com/api/contests/1022/rating/2772?take=5000"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    rating = data["rating"]
    rating = [user for user in rating if user["score"] != 0]

    for user in rating:
        user["calculated_rating"] = user["time"] * 0.7 + user["score"] * 0.3 / 100

    sorted_rating = sorted(rating, key=lambda x: x["calculated_rating"])

    for index, user in enumerate(sorted_rating[:10]):
        print(f"{index + 1}: {user['name']}, Rate: {user['calculated_rating']}, "
              f"Time: {user['time']}, Score: {user['score']}")

else:
    print(f"Error {response.status_code}")
