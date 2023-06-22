def convert_utc_offset_to_time_zone(utc_offset):
    sign = '-' if utc_offset < 0 else '+'
    utc_offset = abs(utc_offset)
    hours = str(utc_offset // 3600).zfill(2)
    minutes = str(utc_offset % 3600 // 60).zfill(2)
    return f'{sign}{hours}:{minutes}'
