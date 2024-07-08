import simpy
from shapely.geometry import Point, LineString, Polygon
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.distance import distance
import folium
from IPython.display import display

# Step 1: Define the Route (user input as city names)
geolocator = Nominatim(user_agent="toll_simulation")

def get_city_location(city_name):
    location = geolocator.geocode(city_name)
    if location:
        return Point(location.longitude, location.latitude)
    else:
        print(f"Could not find location for {city_name}. Please enter a valid city name.")
        return None

# Get starting city location
start_city = input("Enter starting city (e.g., Ahmedabad): ")
start_point = get_city_location(start_city)
while not start_point:
    start_city = input("Enter starting city (e.g., Ahmedabad): ")
    start_point = get_city_location(start_city)

# Get destination city location
end_city = input("Enter destination city (e.g., Delhi): ")
end_point = get_city_location(end_city)
while not end_point:
    end_city = input("Enter destination city (e.g., Delhi): ")
    end_point = get_city_location(end_city)

# Calculate total distance
total_distance = distance((start_point.y, start_point.x), (end_point.y, end_point.x)).km

# Print total distance
print(f"Total distance between {start_city} and {end_city}: {total_distance:.2f} kilometers")

# Step 2: Simulate Vehicle Movement
total_toll_charges = 0.0  # Variable to track total toll charges deducted

def simulate_vehicle_movement(env, start_loc, end_loc, speed, user_account):
    global total_toll_charges
    current_loc = start_loc
    while current_loc.distance(end_loc) > 0.1:
        # Move towards the destination
        direction_vector = LineString([current_loc, end_loc]).parallel_offset(distance=speed, side='right').coords[1]
        new_loc = Point(direction_vector)

        # Calculate distance traveled in this step
        step_distance = current_loc.distance(new_loc)

        # Calculate toll charge for this step
        toll_charge = calculate_toll_charge(step_distance)
        total_toll_charges += toll_charge  # Accumulate total toll charges
        simulate_payment(env, toll_charge, user_account)

        current_loc = new_loc
        yield env.timeout(1)  # Simulate time passing

    print("Vehicle reached destination.")

# Step 3: Calculate Toll Charges
toll_rate_per_km = 15.25  # Example toll rate per kilometer

def calculate_toll_charge(distance):
    return toll_rate_per_km * distance

# Step 4: Simulate Payment
class UserAccount:
    def __init__(self, initial_balance):
        self.balance = initial_balance

    def deduct_balance(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            return True
        else:
            return False

# Step 5: Main Simulation Setup
def main():
    initial_balance = float(input("Enter initial balance for the user account: "))
    user_account = UserAccount(initial_balance)  # Create user account with initial balance

    env = simpy.Environment()
    env.process(simulate_vehicle_movement(env, start_point, end_point, speed=0.5, user_account=user_account))
    env.run(until=2)  # Run simulation for 20 time units

    # Display total toll charges and remaining balance
    print(f"\nTotal toll charges deducted: ${total_toll_charges:.2f}")
    print(f"Remaining balance in user's account: ${user_account.balance:.2f}")

    # Plot the route on a map using Folium
    route_map = folium.Map(location=[start_point.y, start_point.x], zoom_start=6)
    folium.Marker([start_point.y, start_point.x], popup=start_city).add_to(route_map)
    folium.Marker([end_point.y, end_point.x], popup=end_city).add_to(route_map)
    folium.PolyLine(locations=[[start_point.y, start_point.x], [end_point.y, end_point.x]], color='blue').add_to(route_map)

    # Display the map directly in the output
    display(route_map)

# Step 6: Simulate Payment
def simulate_payment(env, toll_charge, user_account):
    if user_account.deduct_balance(toll_charge):
        print(f"Toll charge of ${toll_charge:.2f} deducted from user's account. Remaining balance: ${user_account.balance:.2f}")
    else:
        print(f"Insufficient balance to deduct toll charge of ${toll_charge:.2f}. Remaining balance: ${user_account.balance:.2f}")

if __name__ == "__main__":
    main()
