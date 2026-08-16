"""
Centralized State, District, and Geospatial Coordinates Registry
"""

STATE_DISTRICT_MAP = {
    "Karnataka": [
        "Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Mangaluru (Dakshina Kannada)",
        "Belagavi", "Hubballi-Dharwad", "Tumakuru", "Shivamogga", "Ballari", "Kalaburagi",
        "Udupi", "Hassan", "Mandya", "Davanagere", "Chitradurga", "Kolar",
        "Chikkaballapura", "Bidar", "Raichur", "Koppal", "Bagalkot", "Vijayapura",
        "Gadag", "Haveri", "Uttara Kannada", "Kodagu", "Chamarajanagar", "Yadgir",
        "Ramanagara", "Vijayanagara"
    ],
    "Maharashtra": [
        "Mumbai City", "Mumbai Suburban", "Pune", "Thane", "Nagpur", "Nashik",
        "Chhatrapati Sambhaji Nagar (Aurangabad)", "Solapur", "Kolhapur", "Amravati",
        "Nanded", "Latur", "Satara", "Sangli", "Ahmednagar", "Jalgaon"
    ],
    "Tamil Nadu": [
        "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Tiruppur",
        "Erode", "Vellore", "Kanchipuram", "Tirunelveli", "Thanjavur", "Dharmapuri"
    ],
    "Delhi": [
        "New Delhi", "Central Delhi", "North Delhi", "South Delhi", "East Delhi",
        "West Delhi", "North West Delhi", "South West Delhi", "North East Delhi", "Shahdara"
    ],
    "Telangana": [
        "Hyderabad", "Rangareddy", "Medchal-Malkajgiri", "Warangal", "Karimnagar",
        "Nizamabad", "Khammam", "Nalgonda", "Mahabubnagar", "Adilabad"
    ],
    "Kerala": [
        "Thiruvananthapuram", "Ernakulam (Kochi)", "Kozhikode", "Thrissur", "Kollam",
        "Kannur", "Alappuzha", "Palakkad", "Kottayam", "Malappuram", "Wayanad"
    ],
    "Gujarat": [
        "Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar",
        "Junagadh", "Gandhinagar", "Anand", "Kutch", "Mehsana"
    ]
}


DISTRICT_COORDS = {
    # Karnataka
    "Bengaluru Urban": {"lat": 12.9716, "lon": 77.5946},
    "Bengaluru Rural": {"lat": 13.2257, "lon": 77.5750},
    "Mysuru": {"lat": 12.2958, "lon": 76.6394},
    "Mangaluru (Dakshina Kannada)": {"lat": 12.9141, "lon": 74.8560},
    "Belagavi": {"lat": 15.8497, "lon": 74.4977},
    "Hubballi-Dharwad": {"lat": 15.3647, "lon": 75.1240},
    "Tumakuru": {"lat": 13.3379, "lon": 77.1173},
    "Shivamogga": {"lat": 13.9299, "lon": 75.5681},
    "Ballari": {"lat": 15.1394, "lon": 76.9214},
    "Kalaburagi": {"lat": 17.3297, "lon": 76.8343},
    "Udupi": {"lat": 13.3409, "lon": 74.7421},
    "Hassan": {"lat": 13.0072, "lon": 76.0963},
    "Mandya": {"lat": 12.5218, "lon": 76.8951},
    "Davanagere": {"lat": 14.4644, "lon": 75.9218},
    "Chitradurga": {"lat": 14.2251, "lon": 76.3980},
    "Kolar": {"lat": 13.1367, "lon": 78.1291},
    "Chikkaballapura": {"lat": 13.4355, "lon": 77.7315},
    "Bidar": {"lat": 17.9104, "lon": 77.5199},
    "Raichur": {"lat": 16.2076, "lon": 77.3556},
    "Koppal": {"lat": 15.3486, "lon": 76.1562},
    "Bagalkot": {"lat": 16.1852, "lon": 75.6961},
    "Vijayapura": {"lat": 16.8302, "lon": 75.7100},
    "Gadag": {"lat": 15.4319, "lon": 75.6322},
    "Haveri": {"lat": 14.7947, "lon": 75.3999},
    "Uttara Kannada": {"lat": 14.8050, "lon": 74.1240},
    "Kodagu": {"lat": 12.4244, "lon": 75.7382},
    "Chamarajanagar": {"lat": 11.9261, "lon": 76.9437},
    "Yadgir": {"lat": 16.7640, "lon": 77.1357},
    "Ramanagara": {"lat": 12.7161, "lon": 77.2820},
    "Vijayanagara": {"lat": 15.2716, "lon": 76.3883},

    # Maharashtra
    "Mumbai City": {"lat": 18.9388, "lon": 72.8353},
    "Mumbai Suburban": {"lat": 19.1176, "lon": 72.8481},
    "Pune": {"lat": 18.5204, "lon": 73.8567},
    "Thane": {"lat": 19.2183, "lon": 72.9781},
    "Nagpur": {"lat": 21.1458, "lon": 79.0882},
    "Nashik": {"lat": 19.9975, "lon": 73.7898},
    "Chhatrapati Sambhaji Nagar (Aurangabad)": {"lat": 19.8762, "lon": 75.3433},
    "Solapur": {"lat": 17.6599, "lon": 75.9064},
    "Kolhapur": {"lat": 16.7050, "lon": 74.2433},
    "Amravati": {"lat": 20.9374, "lon": 77.7796},
    "Nanded": {"lat": 19.1383, "lon": 77.3210},
    "Latur": {"lat": 18.4088, "lon": 76.5604},
    "Satara": {"lat": 17.6805, "lon": 74.0183},
    "Sangli": {"lat": 16.8524, "lon": 74.5815},
    "Ahmednagar": {"lat": 19.0948, "lon": 74.7480},
    "Jalgaon": {"lat": 21.0077, "lon": 75.5626},

    # Tamil Nadu
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Coimbatore": {"lat": 11.0168, "lon": 76.9558},
    "Madurai": {"lat": 9.9252, "lon": 78.1198},
    "Tiruchirappalli": {"lat": 10.7905, "lon": 78.7047},
    "Salem": {"lat": 11.6643, "lon": 78.1460},
    "Tiruppur": {"lat": 11.1085, "lon": 77.3411},
    "Erode": {"lat": 11.3410, "lon": 77.7172},
    "Vellore": {"lat": 12.9165, "lon": 79.1325},
    "Kanchipuram": {"lat": 12.8342, "lon": 79.7036},
    "Tirunelveli": {"lat": 8.7139, "lon": 77.7567},
    "Thanjavur": {"lat": 10.7870, "lon": 79.1378},
    "Dharmapuri": {"lat": 12.1211, "lon": 78.1582},

    # Delhi
    "New Delhi": {"lat": 28.6139, "lon": 77.2090},
    "Central Delhi": {"lat": 28.6443, "lon": 77.2182},
    "North Delhi": {"lat": 28.6853, "lon": 77.1723},
    "South Delhi": {"lat": 28.5434, "lon": 77.2423},
    "East Delhi": {"lat": 28.6277, "lon": 77.2955},
    "West Delhi": {"lat": 28.6401, "lon": 77.1087},
    "North West Delhi": {"lat": 28.7289, "lon": 77.1265},
    "South West Delhi": {"lat": 28.5714, "lon": 77.0734},
    "North East Delhi": {"lat": 28.6946, "lon": 77.2694},
    "Shahdara": {"lat": 28.6703, "lon": 77.2894},

    # Telangana
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "Rangareddy": {"lat": 17.2473, "lon": 78.1504},
    "Medchal-Malkajgiri": {"lat": 17.5472, "lon": 78.4869},
    "Warangal": {"lat": 17.9689, "lon": 79.5941},
    "Karimnagar": {"lat": 18.4386, "lon": 79.1288},
    "Nizamabad": {"lat": 18.6725, "lon": 78.0941},
    "Khammam": {"lat": 17.2473, "lon": 80.1514},
    "Nalgonda": {"lat": 17.0577, "lon": 79.2684},
    "Mahabubnagar": {"lat": 16.7488, "lon": 77.9840},
    "Adilabad": {"lat": 19.6641, "lon": 78.5320},

    # Kerala
    "Thiruvananthapuram": {"lat": 8.5241, "lon": 76.9366},
    "Ernakulam (Kochi)": {"lat": 9.9816, "lon": 76.2999},
    "Kozhikode": {"lat": 11.2588, "lon": 75.7804},
    "Thrissur": {"lat": 10.5276, "lon": 76.2144},
    "Kollam": {"lat": 8.8932, "lon": 76.6141},
    "Kannur": {"lat": 11.8745, "lon": 75.3704},
    "Alappuzha": {"lat": 9.4981, "lon": 76.3388},
    "Palakkad": {"lat": 10.7867, "lon": 76.6548},
    "Kottayam": {"lat": 9.5916, "lon": 76.5222},
    "Malappuram": {"lat": 11.0729, "lon": 76.0740},
    "Wayanad": {"lat": 11.6854, "lon": 76.1320},

    # Gujarat
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714},
    "Surat": {"lat": 21.1702, "lon": 72.8311},
    "Vadodara": {"lat": 22.3072, "lon": 73.1812},
    "Rajkot": {"lat": 22.3039, "lon": 70.8022},
    "Bhavnagar": {"lat": 21.7645, "lon": 72.1519},
    "Jamnagar": {"lat": 22.4707, "lon": 70.0577},
    "Junagadh": {"lat": 21.5222, "lon": 70.4579},
    "Gandhinagar": {"lat": 23.2156, "lon": 72.6369},
    "Anand": {"lat": 22.5645, "lon": 72.9289},
    "Kutch": {"lat": 23.7337, "lon": 69.8597},
    "Mehsana": {"lat": 23.6000, "lon": 72.4000}
}
