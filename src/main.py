from src.GeneralPreprocessor import GeneralPreprocessor


def main():
    # Create an instance of GeneralPreprocessor and passing the path of raw data
    pre_processor = GeneralPreprocessor("../raw/Dataset.xlsx")
    # Getting cleaned data set in pd.DataFrame
    cleaned_data_frame = pre_processor.get_cleaned_data()
    # Storing cleaned dataset
    pre_processor.save_to_excel("../out/CleanedDataset.xlsx", cleaned_data_frame)
    print("Done")


if __name__ == '__main__':
    main()
