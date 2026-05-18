import components

if __name__ == "__main__":
    # 测试 DataReceiverParse
    
    parser = components.DataReceiverParse(data_format="csv")
    parser.sensor_config = {
        "温湿度传感器": [
            {"name": "温度", "unit": "℃"},
            {"name": "湿度", "unit": "%"}
        ],
        "气体传感器": [
            {"name": "CO2", "unit": "ppm"},
            {"name": "TVOC", "unit": "ppb"}
        ]
    }
    
    test_data = "25.3,60,400,150"
    result = parser.parse_csv_data(test_data)
    print(result)