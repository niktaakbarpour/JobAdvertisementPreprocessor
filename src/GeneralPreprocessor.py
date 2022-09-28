import pandas as pd
import numpy as np
import re
from pandas import ExcelWriter
from parsivar import Normalizer
from googletrans import Translator
from persiantools.jdatetime import JalaliDate
from sklearn.impute import SimpleImputer
from src.Lexicon import Lexicon


class GeneralPreprocessor:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.persian_normalizer = Normalizer()
        self.translator = Translator()
        self.persian_regex = re.compile("[\u0600-\u06FF\u0750-\u077F\u0590-\u05FF\uFE70-\uFEFF]")
        self.city_lexicon = Lexicon("../raw/CityLexicon.txt")
        self.keyword_lexicon = Lexicon("../raw/KeywordLexicon.txt")

    def get_cleaned_data(self) -> pd.DataFrame:
        data = self._read_data()
        data = self._clean(data)
        data = self._extract_more_keywords(data)
        data = self._fill_missing_value(data)
        return data

    def save_to_excel(self, file_name: str, data: pd.DataFrame = None):
        if data is None:
            data = self.get_cleaned_data()
        data["Keywords"] = data["Keywords"].apply(lambda keywords: "|".join(keywords))
        writer = ExcelWriter(file_name)
        data.to_excel(writer)
        writer.save()

    def _read_data(self) -> pd.DataFrame:
        return pd.read_excel(self.file_name) \
            .dropna(how="all") \
            .dropna(how="all", axis="columns") \
            .reset_index(drop=True)

    def _clean(self, data: pd.DataFrame) -> pd.DataFrame:
        data["CompanyName"] = data["CompanyName"].apply(self._clean_company_name)
        data["CompanyType"] = data["CompanyType"].apply(self._clean_company_type)
        data["AdDate"] = data["AdDate"].apply(self._clean_ad_date)
        data["JobTitle"] = data["JobTitle"].apply(self._translate)
        data["Remote"] = data["Remote"].apply(self._convert_to_boolean)
        data["City"] = data["City"].apply(self._clean_city)
        data["KnowledgeBase"] = data["KnowledgeBase"].apply(self._convert_to_boolean)
        data["FullTime"] = data["FullTime"].apply(self._convert_to_boolean)
        data["Gender"] = data["Gender"].apply(self._clean_gender)
        data["Project"] = data["Project"].apply(self._convert_to_boolean)
        data["Military"] = data["Military"].apply(self._convert_to_boolean)
        data["AdText"] = data["AdText"].apply(self._translate)
        data["Keywords"] = data["Keywords"].apply(self._clean_keywords)
        return data

    def _extract_more_keywords(self, data: pd.DataFrame) -> pd.DataFrame:
        all_keywords = set()
        for keywords in data["Keywords"]:
            if not pd.isna(keywords):
                all_keywords = all_keywords.union(keywords)

        for index in range(len(data)):
            text = self._clean_keywords(data.iloc[index]["AdText"])
            if not pd.isna(text):
                additional_keywords = set()
                for keyword in all_keywords:
                    if keyword in text:
                        additional_keywords.add(keyword)
                if additional_keywords:
                    last_keywords = data.iloc[index]["Keywords"]
                    if pd.isna(last_keywords):
                        last_keywords = set()
                    data.at[index, "Keywords"] = last_keywords.union(additional_keywords)
        return data

    @staticmethod
    def _fill_missing_value(data: pd.DataFrame) -> pd.DataFrame:
        def fill(imputing, column):
            size = len(column)
            reshaped_data = np.reshape(column.values, [size, 1])
            filled_data = imputing.fit_transform(reshaped_data)
            return filled_data

        data["CompanyName"] = fill(SimpleImputer(strategy="constant", fill_value="UNKNOWN COMPANY"), data["CompanyName"])
        data["CompanyType"] = fill(SimpleImputer(strategy="most_frequent"), data["CompanyType"])
        data["AdDate"] = fill(SimpleImputer(strategy="most_frequent"), data["AdDate"])
        data["JobTitle"] = fill(SimpleImputer(strategy="constant", fill_value="EMPTY TITLE"), data["JobTitle"])
        data["Remote"] = fill(SimpleImputer(strategy="most_frequent"), data["Remote"])
        data["City"] = fill(SimpleImputer(strategy="most_frequent"), data["City"])
        data["KnowledgeBase"] = fill(SimpleImputer(strategy="most_frequent"), data["KnowledgeBase"])
        data["FullTime"] = fill(SimpleImputer(strategy="most_frequent"), data["FullTime"])
        data["Gender"] = fill(SimpleImputer(strategy="most_frequent"), data["Gender"])
        data["Project"] = fill(SimpleImputer(strategy="most_frequent"), data["Project"])
        data["Military"] = fill(SimpleImputer(strategy="most_frequent"), data["Military"])
        data["AdText"] = fill(SimpleImputer(strategy="constant", fill_value="EMPTY BODY"), data["AdText"])
        data.dropna(subset=["Keywords"], inplace=True)
        data.reset_index(drop=True, inplace=True)
        return data

    def _translate(self, text):
        if pd.isna(text) or not text:
            return np.nan
        elif self._contain_persian(text):
            return self.translator.translate(self._fix_persian(text), src="fa", dest="en").text.lower()
        else:
            return text

    def _contain_persian(self, text):
        return bool(re.search(self.persian_regex, text))

    def _fix_persian(self, cell) -> str:
        return re.sub('[\u200c]', ' ', self.persian_normalizer.normalize(str(cell)))

    @staticmethod
    def _clean_company_name(company_name):
        if pd.isna(company_name) or not company_name:
            return np.nan
        else:
            return re.sub("\n", ' ', company_name).strip()

    @staticmethod
    def _clean_company_type(company_type):
        if pd.isna(company_type) or not company_type:
            return np.nan
        else:
            company_type = company_type.strip().lower()
            if company_type.startswith("p"):
                return "PRIVATE"
            elif company_type.startswith("g"):
                return "GOVERNMENT"
            elif company_type.startswith("n"):
                return "NONE"
            else:
                return np.nan

    @staticmethod
    def _clean_ad_date(date):
        if pd.isna(date) or not date:
            return np.nan
        else:
            try:
                date = str(date).strip()
                date = re.sub("−", "-", date)
                date = re.sub("/", "-", date)
                split = re.split("-", date)
                if len(split) == 2:
                    year = int(split[0])
                    month = int(split[1])
                    if year < 12 < month:
                        year, month = month, year
                    if year < 1300:
                        year += 1300
                    return JalaliDate(year, month, 1).to_gregorian()
                else:
                    return np.nan
            except:
                return np.nan

    @staticmethod
    def _convert_to_boolean(text):
        if pd.isna(text) or not text:
            return np.nan
        else:
            text = text.strip().lower()
            if text.startswith("y"):
                return 1
            elif text.startswith("n"):
                return 0
            else:
                return np.nan

    def _clean_city(self, city):
        if pd.isna(city) or not city:
            return np.nan
        else:
            return self.city_lexicon.translate(city)

    @staticmethod
    def _clean_gender(gender):
        if pd.isna(gender) or not gender:
            return np.nan
        else:
            text = gender.strip().lower()
            if text.startswith("m"):
                return "MALE"
            elif text.startswith("f"):
                return "FEMALE"
            elif text.startswith("b"):
                return "BOTH"
            else:
                return np.nan

    def _clean_keywords(self, keywords):
        if pd.isna(keywords) or not keywords:
            return np.nan
        else:
            keywords = keywords.strip()
            keywords = re.sub(",", " ", keywords)
            keywords = re.sub("،", " ", keywords)
            keywords = re.sub("/", "-", keywords)
            keywords = re.sub("و", " ", keywords)
            keywords = re.sub("\n", " ", keywords)
            keywords = re.sub("\"", "", keywords)
            keywords = re.sub("•", "", keywords)
            keywords = re.split(" ", keywords)

            def clean_each_keyword(keyword):
                keyword = keyword \
                    .strip() \
                    .lower() \
                    .removeprefix("-") \
                    .removeprefix("'") \
                    .removeprefix("(") \
                    .removesuffix("-") \
                    .removesuffix(")") \
                    .removesuffix(".")
                return self.keyword_lexicon.translate(keyword)

            keywords = set(map(clean_each_keyword, keywords))
            temp = set()
            for word in keywords:
                temp = temp.union(word.split("|"))
            keywords = temp
            keywords = set(filter(lambda w: w and not self._contain_persian(w), keywords))

            if keywords:
                return keywords
            else:
                return np.nan
