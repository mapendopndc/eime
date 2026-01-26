import pandas as pd
import numpy as np
from libraries import TimberDesign

load_combos_array =[
    [1.4,0,0],
    [1.25,1.5,1],
    [1.25,1,1.5]
]

load_combo_names = [
    "ULS 1",
    "ULS 2",
    "ULS 3",
]

load_combos = pd.DataFrame(load_combos_array, columns=['Dead', 'Live', 'Snow'])


#beam_ids = [344] #mid supported
# L2 B320 heavy simply supported
# T/O Pent B2 #mid supported
# T/O Pent B23 # cantilevered

results = {}

# list of kds
def addKD(DL, LL, SL, ForceType):
    PL = DL + 0.25 * LL
    PS1 = SL
    PS2 = LL
    PS3 = SL + 0.5*LL
    PS4 = 0.5*SL + LL
    results.setdefault("PL - " + ForceType, []).extend([PL, PL, PL, PL])
    results.setdefault("PS - " + ForceType, []).extend([PS1, PS2, PS3, PS4])

def addProperty(propType, propValue):
    results.setdefault(propType, []).extend([propValue,propValue,propValue,propValue])

def addLoading(loadID, ufLoads, factors):
    fLoad = ufLoads[0][loadID] * factors[0] + ufLoads[1][loadID] * factors[1] + ufLoads[2][loadID] * factors[2]
    results.setdefault(loadID + "f", []).extend([fLoad,fLoad,fLoad,fLoad])
    return fLoad

def addAppliedLoad(loadDir, stationIdx, numStations, stepSize):
    
    St_1 = results["Station"][-1]
    V_1 = results[loadDir + "f"][-1]

    if (stationIdx == 0):
        results.setdefault("UDL " + loadDir, []).extend([0, 0, 0, 0])
        results.setdefault("PL " + loadDir, []).extend([-V_1, -V_1, -V_1, -V_1])
        return
    
    St_2 = results["Station"][-stepSize-1]

    V_2 = results[loadDir + "f"][-stepSize-1]
    UDL_2 = results["UDL " + loadDir][-stepSize-1+4]

    if (St_1 == St_2):
        results.setdefault("UDL " + loadDir, []).extend([UDL_2, UDL_2, UDL_2, UDL_2])
        pl = V_2 - V_1
        results.setdefault("PL " + loadDir, []).extend([pl, pl, pl, pl])
        return
    
    UDL = (V_1 - V_2) / (St_1 - St_2)
    
    results.setdefault("UDL " + loadDir, []).extend([UDL, UDL, UDL, UDL])

    if (stationIdx == numStations - 1):
        results.setdefault("PL " + loadDir, []).extend([V_1, V_1, V_1, V_1])
    else:
        results.setdefault("PL " + loadDir, []).extend([0, 0, 0, 0])

def process_etabsdata(df): 
    data = df.drop(index=0)
    data.reset_index(drop=True, inplace=True)
    beam_ids = data["Unique Name"].unique()
    for id in beam_ids:
        # Get Beam
        beam_data = data[data["Unique Name"] == id]

        # Get some properties of the beam
        beam_id = beam_data.iloc[0]["Unique Name"]
        beam_name = beam_data.iloc[0]["Beam"]
        beam_story = beam_data.iloc[0]["Story"]
        beam_length = beam_data["Station"].max()

        # Group rows with the same output case
        beam_DL_data = beam_data[beam_data["Output Case"] == "Dead + Super Dead"]
        beam_LL_data = beam_data[beam_data["Output Case"] == "Live"]
        beam_SL_data = beam_data[beam_data["Output Case"] == "Snow"]

        # Check if number of stations is the same for all load patterns
        stations_numbers = [len(beam_DL_data),len(beam_LL_data),len(beam_SL_data)]
        if len(set(stations_numbers)) != 1:
            raise Exception("Number of stations differ across load pattern")
        

        start_pos = 0
        start_pos2 = 0
        start_pos3 = 0
        sum_G = np.zeros(len(load_combos_array))
        Wf = np.zeros(len(load_combos_array))
        end_pos = len(beam_DL_data)
        # Loop through every station
        for i in range(end_pos): #yuk make this better
            station_DL = beam_DL_data.iloc[i]
            station_LL = beam_LL_data.iloc[i]
            station_SL = beam_SL_data.iloc[i]

            beam_station = station_DL["Station"]

            # Loop through every load combination
            for idx in range(len(load_combos)):
                # Add Properties
                addProperty("Story", beam_story)
                addProperty("Beam", beam_name)
                addProperty("Beam Id", beam_id)
                addProperty("Station", beam_station)
                addProperty("Lu", beam_station)
                addProperty("Length", beam_length)
                addProperty("Load Combination", load_combo_names[idx])

                # Add Kd Values
                results.setdefault("kD Case", []).extend([1, 2, 3, 4])
                addKD(station_DL["P"],station_LL["P"],station_SL["P"], "P")
                addKD(station_DL["V2"],station_LL["V2"],station_SL["V2"], "V2")
                addKD(station_DL["V3"],station_LL["V3"],station_SL["V3"], "V3")
                addKD(station_DL["M2"],station_LL["M2"],station_SL["M2"], "M2")
                addKD(station_DL["M3"],station_LL["M3"],station_SL["M3"], "M3")

                # Internal Loading
                unfactored_loads = [station_DL,station_LL,station_SL]
                addLoading("P", unfactored_loads, load_combos_array[idx])
                addLoading("V2", unfactored_loads, load_combos_array[idx])

                addProperty("la", 0)
                addProperty("VA", 0)
                addProperty("VB", 0)
                addProperty("VC", 0)
                addProperty("Sum G", 0)
                addProperty("Wf", 0)
                addProperty("Seg", 0)


                addLoading("V3", unfactored_loads, load_combos_array[idx])
                addLoading("M2", unfactored_loads, load_combos_array[idx])
                addLoading("M3", unfactored_loads, load_combos_array[idx])

                addProperty("LM", beam_station)
                #addProperty("St - VA", beam_station)
                #addProperty("St - VB", beam_station)
                # Applied Load
                addAppliedLoad("V2", i, len(beam_DL_data), len(load_combos) * 4)
                addAppliedLoad("V3", i, len(beam_DL_data), len(load_combos) * 4)





                

            # DONE save start pos
            # DONE check if station is the same as next
            # DONE check if difference if positive
            # DONE extract station @ pos
            # DONE substract current station to pas station
            # set that length to all stations between pos and current
            if (i != 0 and station_DL["Station"] == beam_DL_data.iloc[i-1]["Station"]):
                pointLoad = station_DL["V2"] - beam_DL_data.iloc[i-1]["V2"]
                if (pointLoad < 0):
                    distance = station_DL["Station"] - beam_DL_data.iloc[start_pos]["Station"]
                    if distance > 0:
                        res_len = len(results["Lu"])
                        start_splice = res_len - (i - start_pos + 1) * len(load_combos) * 4
                        results["Lu"][start_splice:res_len] = [distance] * ((i - start_pos + 1)*len(load_combos) * 4)
                        start_pos = i
            elif (i != 0 and i == end_pos-1):
                distance = station_DL["Station"] - beam_DL_data.iloc[start_pos]["Station"]
                res_len = len(results["Lu"])
                start_splice = res_len - (i - start_pos + 1) * len(load_combos) * 4
                results["Lu"][start_splice:res_len] = [distance] * ((i - start_pos + 1)*len(load_combos) * 4)
                start_pos = 0



            if (i > 1 and i != (end_pos - 1) and (station_DL["M3"] * beam_DL_data.iloc[i-1]["M3"]) <= 0):
                distance = beam_DL_data.iloc[i-1]["Station"] - beam_DL_data.iloc[start_pos2]["Station"]
                if distance > 0:
                    res_len = len(results["LM"])
                    start_splice = res_len - (i - start_pos2 + 1) * len(load_combos) * 4
                    end_splice = res_len - 1 * len(load_combos) * 4
                    results["LM"][start_splice:end_splice] = [distance] * ((i - start_pos2)*len(load_combos) * 4)
                    start_pos2 = i
            elif (i == end_pos-1):
                distance = station_DL["Station"] - beam_DL_data.iloc[start_pos2]["Station"]
                res_len = len(results["LM"])
                start_splice = res_len - (i - start_pos2 + 1) * len(load_combos) * 4
                results["LM"][start_splice:res_len] = [distance] * ((i - start_pos2 + 1)*len(load_combos) * 4)
                start_pos2 = 0

            # wf
            if (i != 0):
                combos = np.transpose(np.array(load_combos_array))
                distance = station_DL["Station"] - beam_DL_data.iloc[i-1]["Station"]
                ufload = np.array([beam_DL_data.iloc[i]["V2"], beam_LL_data.iloc[i]["V2"], beam_SL_data.iloc[i]["V2"]])
                ufload_prev = np.array([beam_DL_data.iloc[i-1]["V2"], beam_LL_data.iloc[i-1]["V2"], beam_SL_data.iloc[i-1]["V2"]])
                factoredVf =  np.matmul(ufload, combos)
                factoredVf_prev =  np.matmul(ufload_prev, combos)
                Wf += abs((factoredVf + factoredVf_prev) / 2 * distance)
            # calculating the G factor for shear resistance (ideally run a separate loop for every load case)
            if (i != 0 and station_DL["Station"] == beam_DL_data.iloc[i-1]["Station"]):
                pointLoad = station_DL["V2"] - beam_DL_data.iloc[i-1]["V2"]
                if (pointLoad < 0):
                    distance = station_DL["Station"] - beam_DL_data.iloc[start_pos3]["Station"]
                    if distance > 0:
                        res_len = len(results["Seg"])

                        start_idx = start_pos3
                        mid_idx = round((i + start_pos3) / 2)
                        end_idx = i - 1
                        combos = np.transpose(np.array(load_combos_array))
                        ufload_start = np.array([beam_DL_data.iloc[start_idx]["V2"], beam_LL_data.iloc[start_idx]["V2"], beam_SL_data.iloc[start_idx]["V2"]])
                        ufload_mid = np.array([beam_DL_data.iloc[mid_idx]["V2"], beam_LL_data.iloc[mid_idx]["V2"], beam_SL_data.iloc[mid_idx]["V2"]])
                        ufload_end = np.array([beam_DL_data.iloc[end_idx]["V2"], beam_LL_data.iloc[end_idx]["V2"], beam_SL_data.iloc[end_idx]["V2"]])
                        factoredVfA =  np.matmul(ufload_start, combos)
                        factoredVfB =  np.matmul(ufload_end, combos)
                        factoredVfC =  np.matmul(ufload_mid, combos)
                        G = TimberDesign.GFactor(np.asarray(distance), factoredVfA, factoredVfB, factoredVfC)
                        sum_G += G.result

                        start_splice = res_len - (i - start_pos3 + 1) * len(load_combos) * 4
                        
                        results["Seg"][start_splice:res_len] = [start_pos3] * ((i - start_pos3 + 1)*len(load_combos) * 4)
                        results["la"][start_splice:res_len] = [distance] * ((i - start_pos3 + 1)*len(load_combos) * 4)

                        allVfA = [ele for ele in factoredVfA for i in range(4)]
                        allVfB = [ele for ele in factoredVfB for i in range(4)]
                        allVfC = [ele for ele in factoredVfC for i in range(4)]
                        results["VA"][start_splice:res_len] = allVfA * (i - start_pos3 + 1)
                        results["VB"][start_splice:res_len] = allVfB * (i - start_pos3 + 1)
                        results["VC"][start_splice:res_len] = allVfC * (i - start_pos3 + 1)

                        start_pos3 = i
            elif (i > 1 and i != (end_pos - 1) and (station_DL["V2"] * beam_DL_data.iloc[i-1]["V2"]) <= 0):
                distance = beam_DL_data.iloc[i]["Station"] - beam_DL_data.iloc[start_pos3]["Station"]
                if distance > 0:
                    res_len = len(results["Seg"])
                    # if not zero, interpolate to find true axis intercept
                    start_idx = start_pos3
                    mid_idx = round((i + start_pos3) / 2)
                    end_idx = i
                    combos = np.transpose(np.array(load_combos_array))
                    ufload_start = np.array([beam_DL_data.iloc[start_idx]["V2"], beam_LL_data.iloc[start_idx]["V2"], beam_SL_data.iloc[start_idx]["V2"]])
                    ufload_mid = np.array([beam_DL_data.iloc[mid_idx]["V2"], beam_LL_data.iloc[mid_idx]["V2"], beam_SL_data.iloc[mid_idx]["V2"]])
                    ufload_end = np.array([beam_DL_data.iloc[end_idx]["V2"], beam_LL_data.iloc[end_idx]["V2"], beam_SL_data.iloc[end_idx]["V2"]])
                    factoredVfA =  np.matmul(ufload_start, combos)
                    factoredVfB =  np.matmul(ufload_end, combos)
                    factoredVfC =  np.matmul(ufload_mid, combos)
                    G = TimberDesign.GFactor(np.asarray(distance), factoredVfA, factoredVfB, factoredVfC)
                    sum_G += G.result

                    start_splice = res_len - (i - start_pos3 + 1) * len(load_combos) * 4
                    end_splice = res_len - 1 * len(load_combos) * 4

                    results["Seg"][start_splice:end_splice] = [start_pos3] * ((i - start_pos3)*len(load_combos) * 4)
                    results["la"][start_splice:res_len] = [distance] * ((i - start_pos3 + 1)*len(load_combos) * 4)

                    allVfA = [ele for ele in factoredVfA for i in range(4)]
                    allVfB = [ele for ele in factoredVfB for i in range(4)]
                    allVfC = [ele for ele in factoredVfC for i in range(4)]
                    results["VA"][start_splice:end_splice] = allVfA * (i - start_pos3)
                    results["VB"][start_splice:end_splice] = allVfB * (i - start_pos3)
                    results["VC"][start_splice:end_splice] = allVfC * (i - start_pos3)



                    start_pos3 = i
            elif (i != 0 and i == end_pos-1):
                distance = station_DL["Station"] - beam_DL_data.iloc[start_pos3]["Station"]
                res_len = len(results["Seg"])


                start_idx = start_pos3
                mid_idx = round((i + start_pos3) / 2)
                end_idx = i
                combos = np.transpose(np.array(load_combos_array))
                ufload_start = np.array([beam_DL_data.iloc[start_idx]["V2"], beam_LL_data.iloc[start_idx]["V2"], beam_SL_data.iloc[start_idx]["V2"]])
                ufload_mid = np.array([beam_DL_data.iloc[mid_idx]["V2"], beam_LL_data.iloc[mid_idx]["V2"], beam_SL_data.iloc[mid_idx]["V2"]])
                ufload_end = np.array([beam_DL_data.iloc[end_idx]["V2"], beam_LL_data.iloc[end_idx]["V2"], beam_SL_data.iloc[end_idx]["V2"]])
                factoredVfA =  np.matmul(ufload_start, combos)
                factoredVfB =  np.matmul(ufload_end, combos)
                factoredVfC =  np.matmul(ufload_mid, combos)
                
                G = TimberDesign.GFactor(np.asarray(distance), factoredVfA, factoredVfB, factoredVfC)
                sum_G += G.result

                start_splice = res_len - (i - start_pos3 + 1) * len(load_combos) * 4
                results["Seg"][start_splice:res_len] = [start_pos3] * ((i - start_pos3 + 1)*len(load_combos) * 4)
                results["la"][start_splice:res_len] = [distance] * ((i - start_pos3 + 1)*len(load_combos) * 4)

                allVfA = [ele for ele in factoredVfA for i in range(4)]
                allVfB = [ele for ele in factoredVfB for i in range(4)]
                allVfC = [ele for ele in factoredVfC for i in range(4)]
                allG = [ele for ele in sum_G for i in range(4)]
                allWf = [ele for ele in Wf for i in range(4)]
                results["VA"][start_splice:res_len] = allVfA * (i - start_pos3 + 1)
                results["VB"][start_splice:res_len] = allVfB * (i - start_pos3 + 1)
                results["VC"][start_splice:res_len] = allVfC * (i - start_pos3 + 1)
                results["Sum G"][(res_len - (i + 1) * len(load_combos) * 4):res_len] = allG * (i + 1)
                results["Wf"][(res_len - (i + 1) * len(load_combos) * 4):res_len] = allWf * (i + 1)

                start_pos3 = 0
            

    return pd.DataFrame(results)