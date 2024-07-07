import random
import math
import simpy
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point, LineString

# Week 2: Setup and Initial Development
class GPSModule:
    def __init__(self, env):
        self.env = env
        self.location = Point(0, 0)  # Initial location

    def update_location(self):
        # Simulate GPS location update with random values
        self.location = Point(random.uniform(0, 1000), random.uniform(0, 1000))
        yield self.env.timeout(1)  # Simulate time taken to update location
        return self.location

class TollCalculator:
    def __init__(self):
        self.rate_per_km = 0.05  # Example rate

    def calculate_toll(self, distance):
        return distance * self.rate_per_km

# Week 3: Integration and Testing
class Vehicle:
    def __init__(self, env, vehicle_id, gps_module, toll_calculator, initial_balance, owner_name):
        self.env = env
        self.vehicle_id = vehicle_id
        self.gps_module = gps_module
        self.toll_calculator = toll_calculator
        self.previous_location = gps_module.location
        self.total_toll = 0
        self.total_distance = 0  # Track total distance covered
        self.balance = initial_balance  # Driver's initial balance
        self.owner_name = owner_name  # Owner's name

    def calculate_next_distance_and_toll(self):
        next_location = yield self.env.process(self.gps_module.update_location())
        distance_travelled = self.calculate_distance(self.previous_location, next_location)
        toll = self.toll_calculator.calculate_toll(distance_travelled)
        return next_location, distance_travelled, toll

    def update_location_and_calculate_toll(self):
        next_location, distance_travelled, toll = yield self.env.process(self.calculate_next_distance_and_toll())
        self.previous_location = next_location
        return distance_travelled, toll

    def deduct_toll(self, toll):
        if self.balance >= toll:
            self.balance -= toll
            self.total_toll += toll
            return True
        else:
            return False

    @staticmethod
    def calculate_distance(location1, location2):
        # Calculate Euclidean distance for simplicity
        return location1.distance(location2)

# Week 4: Final Development and Deployment
class PaymentGateway:
    def process_payment(self, vehicle, toll):
        if vehicle.deduct_toll(toll):
            print(f"Deducting ${toll:.2f} from vehicle {vehicle.vehicle_id}'s account owned by {vehicle.owner_name}. New balance: ${vehicle.balance:.2f}\n")
            return True
        else:
            print(f"Vehicle {vehicle.vehicle_id} owned by {vehicle.owner_name} has insufficient funds for toll of ${toll:.2f}. Current balance: ${vehicle.balance:.2f}\n")
            return False

class VehicleWithPayment(Vehicle):
    def __init__(self, env, vehicle_id, gps_module, toll_calculator, payment_gateway, initial_balance, owner_name):
        super().__init__(env, vehicle_id, gps_module, toll_calculator, initial_balance, owner_name)
        self.payment_gateway = payment_gateway
        self.locations_visited = [self.previous_location]  # Store initial location

    def update_location_and_process_payment(self):
        distance_travelled, toll = yield self.env.process(self.update_location_and_calculate_toll())
        if self.payment_gateway.process_payment(self, toll):
            self.total_distance += distance_travelled
            self.locations_visited.append(self.previous_location)  # Store visited location
            yield self.env.timeout(1)  # Simulate time taken for payment processing
            return distance_travelled, toll
        else:
            yield self.env.timeout(1)  # Simulate time taken for payment processing
            return 0, 0  # No distance travelled and no toll incurred if payment fails

def plot_vehicle_path(vehicle):
    if len(vehicle.locations_visited) < 2:
        print(f"Not enough points to plot path for vehicle {vehicle.vehicle_id}")
        return
    
    gdf = gpd.GeoDataFrame(geometry=[Point(pt.x, pt.y) for pt in vehicle.locations_visited])
    line = LineString(gdf.geometry)
    gdf = gpd.GeoDataFrame(geometry=[line])
    
    gdf.plot()
    plt.title(f'Vehicle {vehicle.vehicle_id} Path')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True)
    plt.show()

# Main function to run the simulation
def main():
    env = simpy.Environment()
    vehicles = []
    for vehicle_id in range(1, 5):  # Reduced to 4 for simplicity
        owner_name = input(f"Please enter the name for vehicle {vehicle_id}: ")
        initial_balance = float(input(f"Please enter the initial balance for vehicle {vehicle_id}: "))
        vehicles.append(VehicleWithPayment(env, vehicle_id, GPSModule(env), TollCalculator(), PaymentGateway(), initial_balance, owner_name))

    # Simulate for 10 time steps
    def simulation_step(env, vehicles):
        for vehicle in vehicles:
            yield env.process(vehicle.update_location_and_process_payment())
        
    for time_step in range(10):
        print(f"\nTime step {time_step + 1}")
        env.process(simulation_step(env, vehicles))
        env.run(until=env.now + 1)

    # Print total toll and distance covered for each vehicle
    for vehicle in vehicles:
        print(f"Total distance covered by vehicle {vehicle.vehicle_id} owned by {vehicle.owner_name}: {vehicle.total_distance:.2f} km")
        print(f"Total toll for vehicle {vehicle.vehicle_id} owned by {vehicle.owner_name}: ${vehicle.total_toll:.2f}")
        print(f"Final balance for vehicle {vehicle.vehicle_id} owned by {vehicle.owner_name}: ${vehicle.balance:.2f}")
        plot_vehicle_path(vehicle)  # Plot the path of the vehicle

if __name__ == "__main__":
    main()
