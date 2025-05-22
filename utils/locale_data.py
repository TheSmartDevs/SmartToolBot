# locale_data.py
# Copyright @ISmartDevs
# Channel t.me/TheSmartDev

def get_available_locales():
    """Returns a list of available locales for faker API"""
    return [
        "ar_EG", "ar_JO", "ar_SA", "at_AT", "bg_BG", "bn_BD",
        "cs_CZ", "da_DK", "de_AT", "de_CH", "de_DE", "el_CY",
        "el_GR", "en_AU", "en_CA", "en_GB", "en_HK", "en_IN",
        "en_NG", "en_NZ", "en_PH", "en_SG", "en_UG", "en_US",
        "en_ZA", "es_AR", "es_ES", "es_PE", "es_VE", "et_EE",
        "fa_IR", "fi_FI", "fr_BE", "fr_CA", "fr_CH", "fr_FR",
        "he_IL", "hr_HR", "hu_HU", "hy_AM", "id_ID", "is_IS",
        "it_CH", "it_IT", "ja_JP", "ka_GE", "kk_KZ", "ko_KR",
        "lt_LT", "lv_LV", "me_ME", "mn_MN", "ms_MY", "nb_NO",
        "ne_NP", "nl_BE", "nl_NL", "pl_PL", "pt_BR", "pt_PT",
        "ro_MD", "ro_RO", "ru_RU", "sk_SK", "sl_SI", "sr_Cyrl_RS",
        "sr_Latn_RS", "sr_RS", "sv_SE", "th_TH", "tr_TR", "uk_UA",
        "vi_VN", "zh_CN", "zh_TW"
    ]

def get_locale_for_country(alpha_2):
    """Returns the appropriate locale for a given country code"""
    locale = f"{alpha_2.lower()}_{alpha_2.upper()}"
    available_locales = get_available_locales()
    
    if locale in available_locales:
        return locale
    return None