import math
import time

def get_offset_meters(loc1, lat2, lon2):
    avg_lat = math.radians((loc1.lat + lat2) / 2.0)
    dn = (lat2 - loc1.lat) * 111132.95
    de = (lon2 - loc1.lon) * 111132.95 * math.cos(avg_lat)
    return dn, de

def takeoff(vehicle, target_alt):
    print("--- TAKEOFF ---")
    anchor = vehicle.location.global_frame
    yaw_rad = math.radians(vehicle.heading)
    while True:
        curr_alt = vehicle.location.global_relative_frame.alt
        curr_loc = vehicle.location.global_frame
        dn, de = get_offset_meters(anchor, curr_loc.lat, curr_loc.lon)
        
        d_forward = dn * math.cos(yaw_rad) + de * math.sin(yaw_rad)
        d_right = -dn * math.sin(yaw_rad) + de * math.cos(yaw_rad)
        
        # --- NORTH CHANNEL (PITCH) ---
        # Wind is pushing South (dn < 0). 
        # When we are South of the target (dn < 0), we need HIGH gain (kP_push) to return.
        # When we are North of the target (dn > 0), we need LOW gain (kP_return) to avoid overshooting.
        
        if dn < 0: # Blown away by wind (Power needed!)
            kP_pitch = 120.0 
        else:      # Returning or overshot (Smoothness needed)
            kP_pitch = 40.0
            
        p_cmd = 1500 + (d_forward * kP_pitch)

        # --- EAST CHANNEL (ROLL) ---
        # Wind is pushing West (de < 0).
        # When we are West of the target (de < 0), apply stronger pressure to the right.
        
        if de < 0: # Blown away to the West
            kP_roll = 120.0
        else:      # East of Point A
            kP_roll = 40.0
            
        r_cmd = 1500 - (d_right * kP_roll)

        # Limits (1100 - 1900)
        p_cmd = max(min(int(p_cmd), 1900), 1100)
        r_cmd = max(min(int(r_cmd), 1900), 1100)

        # Throttle logic
        throttle = 1680 if curr_alt < target_alt else 1535
        if curr_alt >= target_alt: break

        vehicle.channels.overrides = {'1': r_cmd, '2': p_cmd, '3': throttle, '4': 1500}
        
        print(f"N:{dn:.1f}m (kP:{kP_pitch}) | E:{de:.1f}m (kP:{kP_roll})", end='\r')
        time.sleep(0.05)

def fly_to_target(vehicle, t_lat, t_lon, t_alt):
    print(f"\n--- FLYING TO TARGET ---")
    iterm_fwd, iterm_rgt = 0, 0
    yaw_rad = math.radians(vehicle.heading)

    while True:
        curr_loc = vehicle.location.global_frame
        curr_alt = vehicle.location.global_relative_frame.alt
        dn, de = get_offset_meters(curr_loc, t_lat, t_lon)
        dist = math.sqrt(dn**2 + de**2)

        # 1. ARRIVAL CHECK (Target < 5 meters)
        if dist < 5: 
            print(f"\n[STABLE] Target reached! Error: {dist:.2f}m")
            break

        d_fwd = dn * math.cos(yaw_rad) + de * math.sin(yaw_rad)
        d_rgt = -dn * math.sin(yaw_rad) + de * math.cos(yaw_rad)

        # 2. DYNAMIC BRAKING (Active only if speed > 0.5 m/s)
        # Prevents braking from interfering while "squeezing" the last centimeters
        current_speed = vehicle.groundspeed

        kp = 60.0 # High kP for fighting the wind

        # 3. ULTRA-AGGRESSIVE INTEGRAL (ki = 2.5 for the final 3 meters)
        ki = 2.5 if dist < 3.0 else 0.6
        iterm_fwd += d_fwd * ki
        iterm_rgt += d_rgt * ki
        
        # Raise integral limit to 300 (deep tilt to counteract wind)
        iterm_fwd = max(min(iterm_fwd, 300), -300)
        iterm_rgt = max(min(iterm_rgt, 300), -300)

        # 4. TILT FORMULA (Add braking_force ONLY if flying too fast)
        p_cmd = 1500 - (d_fwd * kp) - iterm_fwd 
        r_cmd = 1500 + (d_rgt * kp) + iterm_rgt

        # Maximum limits (1100 - 1900)
        p_cmd = max(min(int(p_cmd), 1900), 1100)
        r_cmd = max(min(int(r_cmd), 1900), 1100)

        thr = 1545 if curr_alt < t_alt else 1450

        vehicle.channels.overrides = {'1': r_cmd, '2': p_cmd, '3': int(thr), '4': 1500}
        
        print(f"Dist: {dist:.2f}m | Alt: {curr_alt:.1f}m | it_Fwd: {iterm_fwd:.1f} | Spd: {current_speed:.1f}", end='\r')
        time.sleep(0.05)        

def land(vehicle, t_lat, t_lon):
    print("\n--- LANDING ---")
    
    it_f, it_r = 0, 0
    yaw_rad = math.radians(vehicle.heading)
    last_d_fwd, last_d_rgt = 0, 0
   
    while True:
        curr_loc = vehicle.location.global_frame
        curr_alt = vehicle.location.global_relative_frame.alt
        
        dn, de = get_offset_meters(curr_loc, t_lat, t_lon)
        dist = math.sqrt(dn**2 + de**2)

        # 1. TOUCHDOWN (below 0.3m)
        if curr_alt < 0.2:
            vehicle.channels.overrides = {'3': 1000}
            vehicle.armed = False
            print(f"\n[SUCCESS] Touchdown! Final error: {dist:.2f}m")
            break

        # GPS to Body Frame Rotation
        d_fwd = dn * math.cos(yaw_rad) + de * math.sin(yaw_rad)
        d_rgt = -dn * math.sin(yaw_rad) + de * math.cos(yaw_rad)

        # Dynamic PID Gains based on altitude
        if curr_alt < 5.0:
            kp, ki, kd = 40.0, 1.2, 35.0 # KD for stabilization
        else:
            kp, ki, kd = 55.0, 0.6, 15.0

        it_f += d_fwd * ki
        it_r += d_rgt * ki
        
        # Limit Integral (max tilt while maintaining RPM for stability)
        it_f = max(min(it_f + d_fwd * ki * 0.05, 400), -400)
        it_r = max(min(it_r + d_rgt * ki * 0.05, 400), -400)

        # 2. Velocity Calculation (D-term)
        v_fwd = (d_fwd - last_d_fwd) / 0.05
        v_rgt = (d_rgt - last_d_rgt) / 0.05
        
        last_d_fwd, last_d_rgt = d_fwd, d_rgt

        # Tilt formulas (verified SITL polarity)
        p_cmd = 1500 - (d_fwd * kp) - (v_fwd * kd) - it_f
        r_cmd = 1500 + (d_rgt * kp) + (v_rgt * kd) + it_r

        # Anti-windup / Integral bleed when close to center
        if abs(d_fwd) < 0.2: it_f *= 0.98
        if abs(d_rgt) < 0.2: it_r *= 0.98

        # 3. ANTI-DRIFT THROTTLE LOGIC
        if dist > 0.8:
            # If drifting — hover/wait to regain position
            thr = 1440 if curr_alt > 3.0 else 1510 
            state = "CORRECTING"
        else:
            # Smooth descent: throttle increases as the drone approaches the ground
            # The lower the drone, the more throttle is applied (braking the fall)
            # 1420 (fast at altitude) -> 1485 (soft near the ground)
            target_thr = 1475 - max(0, min(75, curr_alt * 6))
            thr = target_thr
            state = "DESCENDING"

        # Limits (1100 - 1900)
        p_cmd = max(min(int(p_cmd), 1900), 1100)
        r_cmd = max(min(int(r_cmd), 1900), 1100)

        vehicle.channels.overrides = {'1': r_cmd, '2': p_cmd, '3': int(thr), '4': 1500}
        
        print(f"[{state}] Dist: {dist:.1f}m | Alt: {curr_alt:.1f}m | P:{p_cmd} R:{r_cmd}", end='\r')
        time.sleep(0.05)