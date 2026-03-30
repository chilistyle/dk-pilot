from src.connection import connect_drone, arm_and_stabilize
from src.mission import mission
from src.__init__ import load_config

def main():
    load_config()

    try:
        # 1. Connection
        vehicle = connect_drone()
        # 2. Pre-flight initialization
        arm_and_stabilize(vehicle)
        # 3. Mission execution (Takeoff and cruise phases can be added here)
        print("Starting mission sequence...")
        mission(vehicle)
        print("\n[SUCCESS] Mission completed successfully.")
    except KeyboardInterrupt:
        print("\nEmergency Stop!")
    finally:
        print("Closing connection.")
        vehicle.channels.overrides = {'3': 1000}
        vehicle.close()  

if __name__ == "__main__":
    main()