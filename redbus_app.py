import streamlit as st
import pandas as pd
import sqlite3
import re


data_text = """
21:45 06:45 9h 29 Seats (8 Single) ₹1,289 Onwards IntrCity SmartBus A/C Seater / Sleeper (2+1) 4.6 716 New Bus Toilet View seats
22:30 06:30 8h 15 Seats (3 Single) ₹1,633 Onwards Jabbar Travels VE A/C Sleeper (2+1) 4.5 975 On Time View seats
21:15 06:00 8h 45m 20 Seats (6 Single) ₹1,539 Onwards IntrCity SmartBus AC Sleeper (2+1) 4.5 632 New Bus On Time View seats
21:10 07:05 9h 55m 26 Seats (7 Single) ₹1,539 Onwards IntrCity SmartBus Bharat Benz A/C Sleeper (2+1) 4.4 665 View seats Try new 5% OFF
20:45 05:50 9h 5m 19 Seats ₹1,777 Onwards SRI SIDDHAN TRAVELS A/C Sleeper (2+1) 4.5 130 New Bus View seats
"""

lines = data_text.strip().split("\n")

bus_data = []
bus_id = 1

for line in lines:
    times = re.findall(r'\b\d{2}:\d{2}\b', line)
    departure = times[0] if len(times) > 0 else None
    arrival = times[1] if len(times) > 1 else None
    
    dur = re.search(r'\b\d+h(?: \d{1,2}m)?\b', line)
    duration = dur.group() if dur else None
    
    seat_match = re.search(r'(\d+) Seats', line)
    seats = int(seat_match.group(1)) if seat_match else None
    
    price_match = re.search(r'₹([\d,]+)', line)
    price = int(price_match.group(1).replace(',', '')) if price_match else None
    
    op_match = re.search(r'₹[\d,]+ Onwards ([A-Za-z ]+?)(?: A/C| AC| VE|$)', line)
    operator = op_match.group(1).strip() if op_match else None
    
    bus_data.append((bus_id, departure, arrival, duration, seats, price, operator))
    bus_id += 1

conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE buses (
    bus_id INTEGER PRIMARY KEY,
    departure TEXT,
    arrival TEXT,
    duration TEXT,
    seats INTEGER,
    price INTEGER,
    operator TEXT
)
""")

cursor.executemany("INSERT INTO buses VALUES (?, ?, ?, ?, ?, ?, ?)", bus_data)
conn.commit()

df = pd.read_sql("SELECT * FROM buses", conn)

st.title("Bus Booking System")
st.write("Filter buses easily")

st.sidebar.header("Filters")


operators = st.sidebar.multiselect(
    "Select Operator", options=df["operator"].unique(), default=df["operator"].unique()
)

times_sorted = sorted(df["departure"].unique())
departure_time = st.sidebar.select_slider("Departure Time", options=times_sorted, value=(times_sorted[0], times_sorted[-1]))

min_price, max_price = int(df["price"].min()), int(df["price"].max())
price_range = st.sidebar.slider("Price Range (₹)", min_price, max_price, (min_price, max_price))


min_seats, max_seats = int(df["seats"].min()), int(df["seats"].max())
seats_range = st.sidebar.slider("Seats Available", min_seats, max_seats, (min_seats, max_seats))


filtered_df = df[
    (df["operator"].isin(operators)) &
    (df["departure"] >= departure_time[0]) &
    (df["departure"] <= departure_time[1]) &
    (df["price"] >= price_range[0]) &
    (df["price"] <= price_range[1]) &
    (df["seats"] >= seats_range[0]) &
    (df["seats"] <= seats_range[1])
]

st.subheader("Available Buses")
st.write(f"### Showing {len(filtered_df)} buses")
st.dataframe(filtered_df, use_container_width=True)

if not filtered_df.empty:
    selected_bus = st.selectbox("Select a bus for details", filtered_df["bus_id"].tolist())
    bus_info = filtered_df[filtered_df["bus_id"] == selected_bus].iloc[0]
    st.markdown(f"""
    ### 🚌 Bus ID: {bus_info['bus_id']}
    - **Operator:** {bus_info['operator']}
    - **Departure:** {bus_info['departure']}
    - **Arrival:** {bus_info['arrival']}
    - **Duration:** {bus_info['duration']}
    - **Price:** ₹{bus_info['price']}
    - **Seats Available:** {bus_info['seats']}
    """)
