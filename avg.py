if __name__ == "__main__":
    data_sum = 0
    counter = 0
    with open("output_files/e2lora_delta_data.txt", "r") as f:
        data = f.readline()
        while data:
            data_sum += float(data)
            counter += 1
            # if counter == 100:
            #     break
            data = f.readline()

    print(data_sum / counter)
