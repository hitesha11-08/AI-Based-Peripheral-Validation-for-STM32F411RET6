def generate_report(status):

    print("\n========================")
    print("PERIPHERAL HEALTH REPORT")
    print("========================")

    if status == -1:

        print("Status : WARNING")
        print("Anomaly detected")

    else:

        print("Status : HEALTHY")