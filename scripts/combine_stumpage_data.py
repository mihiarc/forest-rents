#!/usr/bin/env python3
"""
Combine all parsed stumpage price data into a unified dataset.

This script reads 16 state-level stumpage price CSV files and combines them
into a single unified dataset with a consistent schema.
"""

import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import track

# Import conversion factors
from unit_conversion_factors import convert_to_per_ton, get_cord_to_ton_factor, get_mbf_to_ton_factor

console = Console()

# Base path for raw data
BASE_PATH = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw")

# Unified schema columns
UNIFIED_COLUMNS = [
    'source',           # State abbreviation
    'year',             # Integer year
    'quarter',          # 1-4 or None for annual
    'period_type',      # quarterly, annual, semi-annual
    'region',           # State-specific geographic area
    'county',           # County name (GA only)
    'species',          # Species or species group
    'product_type',     # Standardized product type
    'price_avg',        # Average price (original unit)
    'price_low',        # Low price range (original unit)
    'price_high',       # High price range (original unit)
    'unit',             # Original price unit ($/ton, $/cord, $/mbf)
    'price_per_ton',    # Standardized price in $/ton
    'conversion_factor', # Factor used to convert to $/ton
    'sample_size',      # Number of reports/samples
    'notes',            # Additional info (log_rule, program, etc.)
]


def standardize_product_type(product: str) -> str:
    """Standardize product type names across sources."""
    if pd.isna(product):
        return None

    product = str(product).lower().strip()

    # Sawtimber variants (check before generic 'log' check)
    if any(x in product for x in ['sawtimber', 'sawlog', 'saw log', 'sawlogs']):
        if 'large' in product:
            return 'sawtimber_large'
        elif 'small' in product:
            return 'sawtimber_small'
        return 'sawtimber'

    # Generic logs -> sawtimber
    if product in ['log', 'logs'] or 'hardwood_sawlog' in product or 'softwood_sawlog' in product:
        return 'sawtimber'

    # MBF products are sawtimber
    if product == 'mbf':
        return 'sawtimber'

    # Pulpwood
    if 'pulpwood' in product or 'pulp' in product:
        return 'pulpwood'

    # Chip-n-saw
    if 'chip' in product and 'saw' in product:
        return 'chip-n-saw'

    # Veneer
    if 'veneer' in product:
        return 'veneer'

    # Poles
    if 'pole' in product:
        return 'poles'

    # Firewood/Fuelwood
    if 'firewood' in product or 'fuelwood' in product or ('fuel' in product and 'chip' not in product):
        return 'firewood'

    # Fiber/Fuel combined
    if 'fiber' in product:
        return 'fiber_fuel'

    # Biomass
    if 'biomass' in product:
        return 'biomass'

    # Boltwood
    if 'bolt' in product:
        return 'boltwood'

    # Studwood
    if 'stud' in product:
        return 'studwood'

    # Cordwood
    if 'cordwood' in product or product == 'cord':
        return 'cordwood'

    # Posts
    if 'post' in product:
        return 'posts'

    # Crossties
    if 'crosstie' in product or 'tie' in product:
        return 'crossties'

    # Plylogs
    if 'plylog' in product:
        return 'plylogs'

    # T-wood/Topwood
    if 't-wood' in product or 'topwood' in product:
        return 'topwood'

    # Fuelchips
    if 'fuelchip' in product:
        return 'fuelchips'

    # Stumpage (generic)
    if 'stumpage' in product:
        return 'sawtimber'  # Assume stumpage without qualifier is sawtimber

    # Total/Index
    if 'total' in product or 'index' in product:
        return 'total_index'

    return product


def standardize_unit(unit: str) -> str:
    """Standardize unit names."""
    if pd.isna(unit):
        return None

    unit = str(unit).lower().strip()

    if 'mbf' in unit or 'thousand board' in unit:
        return '$/mbf'
    if 'cord' in unit:
        return '$/cord'
    if 'ton' in unit:
        return '$/ton'

    return unit


def load_michigan():
    """Load Michigan data - NOTE: This is price INDEX data, not actual prices."""
    path = BASE_PATH / "mi_dnr" / "mi_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    # Michigan has price indices, not actual prices
    return pd.DataFrame({
        'source': 'MI',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['market_area'],
        'county': None,
        'species': df['species_group'],
        'product_type': df['product'].apply(lambda x: 'sawtimber' if x == 'SAW' else ('pulpwood' if x == 'PULP' else 'total_index')),
        'price_avg': df['avg_bid_index'],  # This is an index, not price
        'price_low': None,
        'price_high': None,
        'unit': 'index',  # Mark as index
        'sample_size': df['volume'],
        'notes': 'Price index (base=100), not actual price'
    })


def load_minnesota():
    """Load Minnesota data."""
    path = BASE_PATH / "mn_dnr" / "mn_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'MN',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': 'Statewide',
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price'],
        'price_low': None,
        'price_high': None,
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_wisconsin():
    """Load Wisconsin data."""
    path = BASE_PATH / "wi_dnr" / "wi_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'WI',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': df['zone'].apply(lambda x: f"Zone {x}" if str(x).isdigit() else x),
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price'],
        'price_low': None,
        'price_high': None,
        'unit': '$/cord',  # Wisconsin uses cords
        'sample_size': None,
        'notes': df['program'].apply(lambda x: f"Program: {x}")
    })


def load_new_york():
    """Load New York data."""
    path = BASE_PATH / "ny_dec" / "ny_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    # Map season to quarter
    season_to_quarter = {'winter': 1, 'spring': 2, 'summer': 3, 'fall': 4}

    return pd.DataFrame({
        'source': 'NY',
        'year': df['year'],
        'quarter': df['season'].apply(lambda x: season_to_quarter.get(str(x).lower())),
        'period_type': 'semi-annual',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg_median'],
        'price_low': df['price_low_median'],
        'price_high': df['price_high_median'],
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': df['log_rule'].apply(lambda x: f"Log rule: {x}" if pd.notna(x) else None)
    })


def load_pennsylvania():
    """Load Pennsylvania data."""
    path = BASE_PATH / "pa_extension" / "pa_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'PA',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df['price_low'],
        'price_high': df['price_high'],
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': df['sample_size'],
        'notes': None
    })


def load_vermont():
    """Load Vermont data."""
    path = BASE_PATH / "vt_fpr" / "vt_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'VT',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price'],
        'price_low': None,
        'price_high': None,
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': df['sample_size'],
        'notes': None
    })


def load_maine():
    """Load Maine data."""
    path = BASE_PATH / "me_forest_service" / "me_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'ME',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df['price_min'],
        'price_high': df['price_max'],
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': df['num_reports'],
        'notes': None
    })


def load_alabama():
    """Load Alabama data."""
    path = BASE_PATH / "al_forestry" / "al_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'AL',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_arkansas():
    """Load Arkansas data."""
    path = BASE_PATH / "ar_extension" / "ar_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'AR',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_florida():
    """Load Florida data."""
    path = BASE_PATH / "fl_ifas" / "fl_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'FL',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_georgia():
    """Load Georgia data - county-level data."""
    path = BASE_PATH / "ga_dor" / "ga_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'GA',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': 'Statewide',
        'county': df['county'],
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': None,
        'price_high': None,
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': 'County-level fair market values'
    })


def load_louisiana():
    """Load Louisiana data."""
    path = BASE_PATH / "la_forestry" / "la_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'LA',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price'],
        'price_low': None,
        'price_high': None,
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_mississippi():
    """Load Mississippi data."""
    path = BASE_PATH / "ms_extension" / "ms_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'MS',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_south_carolina():
    """Load South Carolina data."""
    path = BASE_PATH / "sc_forestry" / "sc_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'SC',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_texas():
    """Load Texas data."""
    path = BASE_PATH / "texas_am" / "tx_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'TX',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type_normalized'].apply(standardize_product_type) if 'product_type_normalized' in df.columns else df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': None,
        'price_high': None,
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_west_virginia():
    """Load West Virginia data."""
    path = BASE_PATH / "wv_forestry" / "wv_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'WV',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': df.get('num_reports'),
        'notes': None
    })


def load_north_carolina():
    """Load North Carolina data."""
    path = BASE_PATH / "nc_state" / "nc_stumpage_prices_combined.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    # Map product names to standardized format
    def map_product(p):
        if 'sawtimber' in p:
            return 'sawtimber'
        elif 'pulpwood' in p:
            return 'pulpwood'
        return p

    def map_species(p):
        if 'pine' in p:
            return 'Pine'
        elif 'hardwood' in p:
            return 'Hardwood'
        return 'Mixed'

    return pd.DataFrame({
        'source': 'NC',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': df['region'].apply(lambda x: x.replace('_', ' ').title()),
        'county': None,
        'species': df['product'].apply(map_species),
        'product_type': df['product'].apply(map_product),
        'price_avg': df['price'],
        'price_low': None,
        'price_high': None,
        'unit': '$/mbf',  # NC prices are in $/MBF
        'sample_size': None,
        'notes': None
    })


def load_usfs_pnw():
    """Load USFS Pacific Northwest data (OR, WA, MT, ID, CA, AK)."""
    path = BASE_PATH / "usfs_pnw" / "usfs_pnw_stumpage_combined.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    # Map subregions to state codes
    def get_state_code(row):
        subregion = str(row['subregion']).lower()
        region = str(row['region']).lower()

        if 'montana' in subregion:
            return 'MT'
        elif 'idaho' in subregion:
            return 'ID'
        elif 'oregon' in subregion:
            return 'OR'
        elif 'washington' in subregion:
            return 'WA'
        elif 'california' in subregion or 'california' in region:
            return 'CA'
        elif 'alaska' in subregion or 'alaska' in region:
            return 'AK'
        elif 'montana_idaho' in region:
            return 'MT_ID'
        elif 'washington_oregon' in region:
            return 'OR_WA'
        return 'PNW'

    # Create a record for each row with state-level attribution
    records = []
    for _, row in df.iterrows():
        state = get_state_code(row)
        records.append({
            'source': state,
            'year': row['year'],
            'quarter': None,
            'period_type': 'annual',
            'region': row['subregion'],
            'county': None,
            'species': 'Softwood',  # PNW data is primarily softwood/conifer
            'product_type': 'sawtimber',
            'price_avg': row['price_per_mbf'],
            'price_low': None,
            'price_high': None,
            'unit': '$/mbf',
            'sample_size': None,
            'notes': f"USFS PNW; Table: {row['table']}"
        })

    return pd.DataFrame(records)


def load_missouri():
    """Load Missouri MDC data."""
    path = BASE_PATH / "mo_mdc" / "mo_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'MO',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_virginia():
    """Load Virginia Tech data."""
    path = BASE_PATH / "va_tech" / "va_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    # Convert Q1, Q2, etc. to integers
    def parse_quarter(q):
        if pd.isna(q):
            return None
        q_str = str(q).upper()
        if 'Q1' in q_str:
            return 1
        elif 'Q2' in q_str:
            return 2
        elif 'Q3' in q_str:
            return 3
        elif 'Q4' in q_str:
            return 4
        return None

    return pd.DataFrame({
        'source': 'VA',
        'year': df['year'],
        'quarter': df['quarter'].apply(parse_quarter),
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': None,
        'price_high': None,
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_ohio():
    """Load Ohio OSU data."""
    path = BASE_PATH / "oh_osu" / "oh_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    # Convert quarter - Ohio uses 'ANNUAL', 'January', 'July'
    def parse_quarter(q):
        if pd.isna(q):
            return None
        q_str = str(q).upper()
        if 'ANNUAL' in q_str:
            return None
        elif 'JAN' in q_str:
            return 1
        elif 'JUL' in q_str:
            return 3
        return None

    def get_period_type(q):
        if pd.isna(q):
            return 'annual'
        if 'ANNUAL' in str(q).upper():
            return 'annual'
        return 'semi-annual'

    return pd.DataFrame({
        'source': 'OH',
        'year': df['year'],
        'quarter': df['quarter'].apply(parse_quarter),
        'period_type': df['quarter'].apply(get_period_type),
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_indiana():
    """Load Indiana Woodland Stewards data."""
    path = BASE_PATH / "in_woodland" / "in_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'IN',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': None,
        'price_high': None,
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': df.get('quality_grade', None)
    })


def load_kentucky():
    """Load Kentucky Division of Forestry data.

    Note: Kentucky reports DELIVERED log prices, not stumpage prices.
    Stumpage is typically 40-60% of delivered price.
    """
    path = BASE_PATH / "ky_forestry" / "ky_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'KY',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': 'Delivered log price (not stumpage)'
    })


def load_tennessee():
    """Load Tennessee Forest Products Bulletin data.

    Note: Tennessee reports DELIVERED prices to mills, not stumpage.
    To estimate stumpage, subtract approximately:
    - Sawtimber: $60-100/MBF
    - Pulpwood: $12-18/ton
    """
    path = BASE_PATH / "tn_forestry" / "tn_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'TN',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': df['notes']
    })


def load_new_hampshire():
    """Load New Hampshire stumpage data from Figshare research dataset."""
    path = BASE_PATH / "nh_dra" / "nh_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    # Convert Q1, Q2, etc. to integers
    def parse_quarter(q):
        if pd.isna(q):
            return None
        q_str = str(q).upper()
        if 'Q1' in q_str or q_str == '1':
            return 1
        elif 'Q2' in q_str or q_str == '2':
            return 2
        elif 'Q3' in q_str or q_str == '3':
            return 3
        elif 'Q4' in q_str or q_str == '4':
            return 4
        return None

    return pd.DataFrame({
        'source': 'NH',
        'year': df['year'],
        'quarter': df['quarter'].apply(parse_quarter),
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': df.get('notes')
    })


def main():
    console.print("[bold blue]Combining Stumpage Price Data from 21+ States[/bold blue]\n")

    # Define all loaders
    loaders = [
        ('Michigan', load_michigan),
        ('Minnesota', load_minnesota),
        ('Wisconsin', load_wisconsin),
        ('New York', load_new_york),
        ('Pennsylvania', load_pennsylvania),
        ('Vermont', load_vermont),
        ('Maine', load_maine),
        ('Alabama', load_alabama),
        ('Arkansas', load_arkansas),
        ('Florida', load_florida),
        ('Georgia', load_georgia),
        ('Louisiana', load_louisiana),
        ('Mississippi', load_mississippi),
        ('South Carolina', load_south_carolina),
        ('Texas', load_texas),
        ('West Virginia', load_west_virginia),
        ('North Carolina', load_north_carolina),
        ('USFS PNW (OR/WA/MT/ID/CA/AK)', load_usfs_pnw),
        ('Missouri', load_missouri),
        ('Virginia', load_virginia),
        ('Ohio', load_ohio),
        ('Indiana', load_indiana),
        ('Kentucky', load_kentucky),
        ('Tennessee', load_tennessee),
        ('New Hampshire', load_new_hampshire),
    ]

    # Load all data
    all_data = []
    stats = []

    for name, loader in track(loaders, description="Loading state data..."):
        try:
            df = loader()
            if not df.empty:
                all_data.append(df)
                stats.append({
                    'State': name,
                    'Records': len(df),
                    'Years': f"{df['year'].min()}-{df['year'].max()}",
                    'Status': '[green]OK[/green]'
                })
            else:
                stats.append({
                    'State': name,
                    'Records': 0,
                    'Years': '-',
                    'Status': '[yellow]Empty[/yellow]'
                })
        except Exception as e:
            stats.append({
                'State': name,
                'Records': 0,
                'Years': '-',
                'Status': f'[red]Error: {str(e)[:30]}[/red]'
            })

    # Combine all dataframes
    console.print("\n[bold]Combining datasets...[/bold]")
    combined = pd.concat(all_data, ignore_index=True)

    # Ensure all columns exist
    for col in UNIFIED_COLUMNS:
        if col not in combined.columns:
            combined[col] = None

    # Apply unit conversions to standardize prices to $/ton
    console.print("[bold]Standardizing prices to $/ton...[/bold]")

    def get_conversion_factor(row):
        """Get the conversion factor for a row."""
        unit = str(row['unit']).lower() if pd.notna(row['unit']) else ''
        species = str(row['species']) if pd.notna(row['species']) else ''

        if 'ton' in unit:
            return 1.0
        elif 'cord' in unit:
            return get_cord_to_ton_factor(species, row.get('product_type', ''))
        elif 'mbf' in unit:
            return get_mbf_to_ton_factor(species, row.get('product_type', ''))
        elif 'index' in unit:
            return None  # Cannot convert index to actual price
        return None

    def convert_price(row, price_col):
        """Convert a price column to $/ton."""
        if pd.isna(row[price_col]):
            return None
        factor = row['conversion_factor']
        if factor is None or pd.isna(factor):
            return None
        unit = str(row['unit']).lower() if pd.notna(row['unit']) else ''
        if 'ton' in unit:
            return row[price_col]
        elif 'cord' in unit or 'mbf' in unit:
            return row[price_col] / factor
        return None

    # Calculate conversion factors
    combined['conversion_factor'] = combined.apply(get_conversion_factor, axis=1)

    # Calculate standardized price per ton
    combined['price_per_ton'] = combined.apply(lambda r: convert_price(r, 'price_avg'), axis=1)

    # Count conversions
    converted_count = combined['price_per_ton'].notna().sum()
    total_with_price = combined['price_avg'].notna().sum()
    console.print(f"  Converted {converted_count:,} of {total_with_price:,} records to $/ton")

    # Reorder columns
    combined = combined[UNIFIED_COLUMNS]

    # Save combined dataset
    output_path = BASE_PATH.parent / "processed" / "stumpage_unified.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False)

    # Display loading stats
    table = Table(title="Data Loading Summary")
    table.add_column("State", style="cyan")
    table.add_column("Records", justify="right")
    table.add_column("Years", justify="center")
    table.add_column("Status")

    for s in stats:
        table.add_row(s['State'], str(s['Records']), s['Years'], s['Status'])

    console.print(table)

    # Display summary statistics
    console.print(f"\n[bold green]Combined Dataset Summary[/bold green]")
    console.print(f"Total records: {len(combined):,}")
    console.print(f"Output file: {output_path}")

    # Summary by state
    state_summary = combined.groupby('source').agg({
        'year': ['min', 'max', 'count']
    }).round(0)
    state_summary.columns = ['Year Min', 'Year Max', 'Records']

    console.print("\n[bold]Records by State:[/bold]")
    summary_table = Table()
    summary_table.add_column("State", style="cyan")
    summary_table.add_column("Records", justify="right")
    summary_table.add_column("Year Range", justify="center")

    for state in sorted(combined['source'].unique()):
        state_data = combined[combined['source'] == state]
        summary_table.add_row(
            state,
            f"{len(state_data):,}",
            f"{int(state_data['year'].min())}-{int(state_data['year'].max())}"
        )

    console.print(summary_table)

    # Summary by product type
    console.print("\n[bold]Records by Product Type:[/bold]")
    product_counts = combined['product_type'].value_counts()
    for product, count in product_counts.head(15).items():
        console.print(f"  {product}: {count:,}")

    # Summary by unit
    console.print("\n[bold]Records by Unit:[/bold]")
    unit_counts = combined['unit'].value_counts()
    for unit, count in unit_counts.items():
        console.print(f"  {unit}: {count:,}")

    # Standardized price summary
    console.print("\n[bold]Standardized Price Summary ($/ton):[/bold]")
    price_data = combined[combined['price_per_ton'].notna()]
    if len(price_data) > 0:
        console.print(f"  Records with $/ton price: {len(price_data):,}")
        console.print(f"  Mean: ${price_data['price_per_ton'].mean():.2f}/ton")
        console.print(f"  Median: ${price_data['price_per_ton'].median():.2f}/ton")
        console.print(f"  Range: ${price_data['price_per_ton'].min():.2f} - ${price_data['price_per_ton'].max():.2f}/ton")

        # By product type
        console.print("\n[bold]Mean $/ton by Product Type:[/bold]")
        product_prices = price_data.groupby('product_type')['price_per_ton'].agg(['mean', 'count'])
        product_prices = product_prices.sort_values('count', ascending=False).head(10)
        for product, row in product_prices.iterrows():
            console.print(f"  {product}: ${row['mean']:.2f}/ton ({int(row['count']):,} records)")

    # Year coverage
    console.print(f"\n[bold]Year Coverage:[/bold] {int(combined['year'].min())} - {int(combined['year'].max())}")

    return combined


if __name__ == "__main__":
    main()
