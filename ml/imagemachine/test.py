import json
import os

def main():
    filename = 'df_combined_DanLiedPeopleDied_JSON.json'
    # filename = 'jane.txy.json'
    folder = os.path.join(os.getcwd(),"input_data/metadata")
    full_path = os.path.join(folder, filename)
    with open(full_path, 'r', encoding="utf8") as f:
        metadata = json.load(f)
        print(metadata.keys())

def writeJSONToFile(filename, data, mode):
    data = json.dumps(data)
    f = open(filename, mode)
    f.write(data)

if __name__ == "__main__":
    main()