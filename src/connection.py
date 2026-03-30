from dronekit import connect, VehicleMode
import time
import os

def connect_drone():
    # Read parameters (converted to the required data types)
    CONN_STR = os.getenv("CONNECTION_STRING")
    print(f"Connecting to vehicle on: {CONN_STR}")
    vehicle = connect(CONN_STR, wait_ready=True)

    vehicle.parameters['SIM_WIND_SPD'] = float(os.getenv("WIND_SPEED", 4.0))
    vehicle.parameters['SIM_WIND_DIR'] = float(os.getenv("WIND_DIRECTION", 30.0))
    vehicle.parameters['SIM_WIND_TURB'] = float(os.getenv("SIM_WIND_TURB", 2.0))
    vehicle.parameters['SIM_WIND_TURB_FREQ'] = float(os.getenv("SIM_WIND_TURB_FREQ", 0.2))
    return vehicle

def arm_and_stabilize(vehicle):
    print("\n--- PRE-ARMING CHECKS ---")
    
    # 1. Force disable arming checks if needed (SITL Workaround)
    # vehicle.parameters['ARMING_CHECK'] = 0 

    # 2. Wait for the EKF to stabilize sensors (Gyros/Accels)
    print("Waiting for EKF to settle (Gyros/GPS)...")
    while not vehicle.is_armable:
        # Check messages in Mission Planner - 'Gyros inconsistent' usually disappears here
        print(" [INFO] Vehicle not armable yet. Waiting...", end='\r')
        time.sleep(1)
    
    print("\n[READY] Vehicle is armable.")

    # 3. Set mode to STABILIZE
    vehicle.mode = VehicleMode("STABILIZE")
    while vehicle.mode.name != 'STABILIZE':
        print(" Waiting for mode change...")
        time.sleep(0.5)

    # 4. Final Arming Loop
    print("Arming motors...")
    vehicle.armed = True
    
    timeout = 0
    while not vehicle.armed:
        # If it takes too long, re-send the arm command
        if timeout > 10:
            print("\n [RETRY] Re-sending Arm command...")
            vehicle.armed = True
            timeout = 0
        
        print(" [WAITING] Confirming Arming...", end='\r')
        time.sleep(0.5)
        timeout += 1

    print("\n[SUCCESS] Vehicle ARMED and ready for takeoff!")
