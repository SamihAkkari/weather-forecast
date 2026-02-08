import requests



class GetData:
    def __init__(self):
        pass



class WeatherIngestor:
    def __init__(self):
        pass



url = "https://public-api.meteofrance.fr/public/DPPaquetObs/v1/paquet/infrahoraire-6m"

params = {
    "id_station": "01014002",
    "format": "csv"
}

headers = {
    "accept": "*/*",
    "Authorization": "Bearer eyJ4NXQiOiJOelU0WTJJME9XRXhZVGt6WkdJM1kySTFaakZqWVRJeE4yUTNNalEyTkRRM09HRmtZalkzTURkbE9UZ3paakUxTURRNFltSTVPR1kyTURjMVkyWTBNdyIsImtpZCI6Ik56VTRZMkkwT1dFeFlUa3paR0kzWTJJMVpqRmpZVEl4TjJRM01qUTJORFEzT0dGa1lqWTNNRGRsT1RnelpqRTFNRFE0WW1JNU9HWTJNRGMxWTJZME13X1JTMjU2IiwidHlwIjoiYXQrand0IiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiIwMjkwYjA1Ni0wODI5LTQ4OWQtOTYzZS01MGZjY2EyZmQ1ZTciLCJhdXQiOiJBUFBMSUNBVElPTiIsImF1ZCI6Im1kbXpQSU0zcEF6NmZxcVBiTmxCbEwwODRwa2EiLCJuYmYiOjE3NzA1MDIwODgsImF6cCI6Im1kbXpQSU0zcEF6NmZxcVBiTmxCbEwwODRwa2EiLCJzY29wZSI6ImRlZmF1bHQiLCJpc3MiOiJodHRwczpcL1wvcG9ydGFpbC1hcGkubWV0ZW9mcmFuY2UuZnJcL29hdXRoMlwvdG9rZW4iLCJleHAiOjE3NzA1MDU2ODgsImlhdCI6MTc3MDUwMjA4OCwianRpIjoiNzFkYzNjYjctNjVmZC00MmI3LTgxNmQtMjlhNDFiYTNiYzZhIiwiY2xpZW50X2lkIjoibWRtelBJTTNwQXo2ZnFxUGJObEJsTDA4NHBrYSJ9.iIKhUws4NL9-U6nYEyDAjU0syj91hUr11yoD0RVaZ4i13IpV0DQlqXIyJOZpBlBz_JF7CZbuzsXSVGWUpTMFNW2H1gIAkU7TN_FsGt5axYxnCMn7oZ9X4Zym6YT-0n5ulMj12teSr8ojqO9Iz1tjvNlzihHfOl9V9M7O3S7Ayz6zVIzIiQKb7MA7McV7ZXc2VE1ZmM0h69VOpEhVGV1YKygIN4HCm4cXt2RfvROwKncNHgQh_2FGXNHacn-OJ1vgiLiD7BU4lfk9Gp-bVsGP1DY-rVXbr9Ebt5vcXio1FU8g4JmwIEkeW0AZjfFTHnTJ28BjiGu7Er2RXWiHZeatfQ"
}

response = requests.get(url, params=params, headers=headers)

print(response.status_code)

data = response.json()



needed_data = []
for record in data:
    needed_data.append({
        'time': record['validity_time'],
        'temperature': record['t'],
    })

import pandas as pd

df = pd.DataFrame(needed_data)
df["time"] = pd.to_datetime(df["time"])


# Compute differences between consecutive timestamps
df['delta'] = df["time"].diff()

# Convert to seconds (optional)
df['delta_sec'] = df['delta'].dt.total_seconds()

# Quick stats
print(df['delta_sec'].describe())


expected = -6 * 60  # seconds
missing_steps = (df['delta_sec'] != expected).sum()
print("Number of irregular steps:", missing_steps)

duplicates = df["time"].duplicated().sum()
print("Number of repeated timestamps:", duplicates)

df['delta_sec'].hist(bins=50)