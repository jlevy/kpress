"""Pinned GitHub-compatible heading slugger."""

from __future__ import annotations

from bisect import bisect_right

# Generated from github-slugger 2.0.0's regex.js at commit
# 3461c4350868329c8530904d170358bca1d31448. The upstream generator targets
# Unicode 13.0.0. Keeping scalar ranges here makes results independent of the
# Python runtime's evolving Unicode database. The complete upstream fixture
# sequence and ISC notice live under tests/fixtures/github-slugger-2.0.0.
_EXCLUDED_RANGE_SPEC = "0-1f,21-2c,2e-2f,3a-40,5b-5e,60,7b-a9,ab-b4,b6-b9,bb-bf,d7,f7,2c2-2c5,2d2-2df,2e5-2eb,2ed,2ef-2ff,375,378-379,37e,380-385,387,38b,38d,3a2,3f6,482,530,557-558,55a-55f,589-590,5be,5c0,5c3,5c6,5c8-5cf,5eb-5ee,5f3-60f,61b-61f,66a-66d,6d4,6dd-6de,6e9,6fd-6fe,700-70f,74b-74c,7b2-7bf,7f6-7f9,7fb-7fc,7fe-7ff,82e-83f,85c-85f,86b-89f,8b5,8c8-8d2,8e2,964-965,970,984,98d-98e,991-992,9a9,9b1,9b3-9b5,9ba-9bb,9c5-9c6,9c9-9ca,9cf-9d6,9d8-9db,9de,9e4-9e5,9f2-9fb,9fd,9ff-a00,a04,a0b-a0e,a11-a12,a29,a31,a34,a37,a3a-a3b,a3d,a43-a46,a49-a4a,a4e-a50,a52-a58,a5d,a5f-a65,a76-a80,a84,a8e,a92,aa9,ab1,ab4,aba-abb,ac6,aca,ace-acf,ad1-adf,ae4-ae5,af0-af8,b00,b04,b0d-b0e,b11-b12,b29,b31,b34,b3a-b3b,b45-b46,b49-b4a,b4e-b54,b58-b5b,b5e,b64-b65,b70,b72-b81,b84,b8b-b8d,b91,b96-b98,b9b,b9d,ba0-ba2,ba5-ba7,bab-bad,bba-bbd,bc3-bc5,bc9,bce-bcf,bd1-bd6,bd8-be5,bf0-bff,c0d,c11,c29,c3a-c3c,c45,c49,c4e-c54,c57,c5b-c5f,c64-c65,c70-c7f,c84,c8d,c91,ca9,cb4,cba-cbb,cc5,cc9,cce-cd4,cd7-cdd,cdf,ce4-ce5,cf0,cf3-cff,d0d,d11,d45,d49,d4f-d53,d58-d5e,d64-d65,d70-d79,d80,d84,d97-d99,db2,dbc,dbe-dbf,dc7-dc9,dcb-dce,dd5,dd7,de0-de5,df0-df1,df4-e00,e3b-e3f,e4f,e5a-e80,e83,e85,e8b,ea4,ea6,ebe-ebf,ec5,ec7,ece-ecf,eda-edb,ee0-eff,f01-f17,f1a-f1f,f2a-f34,f36,f38,f3a-f3d,f48,f6d-f70,f85,f98,fbd-fc5,fc7-fff,104a-104f,109e-109f,10c6,10c8-10cc,10ce-10cf,10fb,1249,124e-124f,1257,1259,125e-125f,1289,128e-128f,12b1,12b6-12b7,12bf,12c1,12c6-12c7,12d7,1311,1316-1317,135b-135c,1360-137f,1390-139f,13f6-13f7,13fe-1400,166d-166e,1680,169b-169f,16eb-16ed,16f9-16ff,170d,1715-171f,1735-173f,1754-175f,176d,1771,1774-177f,17d4-17d6,17d8-17db,17de-17df,17ea-180a,180e-180f,181a-181f,1879-187f,18ab-18af,18f6-18ff,191f,192c-192f,193c-1945,196e-196f,1975-197f,19ac-19af,19ca-19cf,19da-19ff,1a1c-1a1f,1a5f,1a7d-1a7e,1a8a-1a8f,1a9a-1aa6,1aa8-1aaf,1ac1-1aff,1b4c-1b4f,1b5a-1b6a,1b74-1b7f,1bf4-1bff,1c38-1c3f,1c4a-1c4c,1c7e-1c7f,1c89-1c8f,1cbb-1cbc,1cc0-1ccf,1cd3,1cfb-1cff,1dfa,1f16-1f17,1f1e-1f1f,1f46-1f47,1f4e-1f4f,1f58,1f5a,1f5c,1f5e,1f7e-1f7f,1fb5,1fbd,1fbf-1fc1,1fc5,1fcd-1fcf,1fd4-1fd5,1fdc-1fdf,1fed-1ff1,1ff5,1ffd-203e,2041-2053,2055-2070,2072-207e,2080-208f,209d-20cf,20f1-2101,2103-2106,2108-2109,2114,2116-2118,211e-2123,2125,2127,2129,212e,213a-213b,2140-2144,214a-214d,214f-215f,2189-24b5,24ea-2bff,2c2f,2c5f,2ce5-2cea,2cf4-2cff,2d26,2d28-2d2c,2d2e-2d2f,2d68-2d6e,2d70-2d7e,2d97-2d9f,2da7,2daf,2db7,2dbf,2dc7,2dcf,2dd7,2ddf,2e00-2e2e,2e30-3004,3008-3020,3030,3036-3037,303d-3040,3097-3098,309b-309c,30a0,30fb,3100-3104,3130,318f-319f,31c0-31ef,3200-33ff,4dc0-4dff,9ffd-9fff,a48d-a4cf,a4fe-a4ff,a60d-a60f,a62c-a63f,a673,a67e,a6f2-a716,a720-a721,a789-a78a,a7c0-a7c1,a7cb-a7f4,a828-a82b,a82d-a83f,a874-a87f,a8c6-a8cf,a8da-a8df,a8f8-a8fa,a8fc,a92e-a92f,a954-a95f,a97d-a97f,a9c1-a9ce,a9da-a9df,a9ff,aa37-aa3f,aa4e-aa4f,aa5a-aa5f,aa77-aa79,aac3-aada,aade-aadf,aaf0-aaf1,aaf7-ab00,ab07-ab08,ab0f-ab10,ab17-ab1f,ab27,ab2f,ab5b,ab6a-ab6f,abeb,abee-abef,abfa-abff,d7a4-d7af,d7c7-d7ca,d7fc-d7ff,e000-f8ff,fa6e-fa6f,fada-faff,fb07-fb12,fb18-fb1c,fb29,fb37,fb3d,fb3f,fb42,fb45,fbb2-fbd2,fd3e-fd4f,fd90-fd91,fdc8-fdef,fdfc-fdff,fe10-fe1f,fe30-fe32,fe35-fe4c,fe50-fe6f,fe75,fefd-ff0f,ff1a-ff20,ff3b-ff3e,ff40,ff5b-ff65,ffbf-ffc1,ffc8-ffc9,ffd0-ffd1,ffd8-ffd9,ffdd-ffff,1000c,10027,1003b,1003e,1004e-1004f,1005e-1007f,100fb-1013f,10175-101fc,101fe-1027f,1029d-1029f,102d1-102df,102e1-102ff,10320-1032c,1034b-1034f,1037b-1037f,1039e-1039f,103c4-103c7,103d0,103d6-103ff,1049e-1049f,104aa-104af,104d4-104d7,104fc-104ff,10528-1052f,10564-105ff,10737-1073f,10756-1075f,10768-107ff,10806-10807,10809,10836,10839-1083b,1083d-1083e,10856-1085f,10877-1087f,1089f-108df,108f3,108f6-108ff,10916-1091f,1093a-1097f,109b8-109bd,109c0-109ff,10a04,10a07-10a0b,10a14,10a18,10a36-10a37,10a3b-10a3e,10a40-10a5f,10a7d-10a7f,10a9d-10abf,10ac8,10ae7-10aff,10b36-10b3f,10b56-10b5f,10b73-10b7f,10b92-10bff,10c49-10c7f,10cb3-10cbf,10cf3-10cff,10d28-10d2f,10d3a-10e7f,10eaa,10ead-10eaf,10eb2-10eff,10f1d-10f26,10f28-10f2f,10f51-10faf,10fc5-10fdf,10ff7-10fff,11047-11065,11070-1107e,110bb-110cf,110e9-110ef,110fa-110ff,11135,11140-11143,11148-1114f,11174-11175,11177-1117f,111c5-111c8,111cd,111db,111dd-111ff,11212,11238-1123d,1123f-1127f,11287,11289,1128e,1129e,112a9-112af,112eb-112ef,112fa-112ff,11304,1130d-1130e,11311-11312,11329,11331,11334,1133a,11345-11346,11349-1134a,1134e-1134f,11351-11356,11358-1135c,11364-11365,1136d-1136f,11375-113ff,1144b-1144f,1145a-1145d,11462-1147f,114c6,114c8-114cf,114da-1157f,115b6-115b7,115c1-115d7,115de-115ff,11641-11643,11645-1164f,1165a-1167f,116b9-116bf,116ca-116ff,1171b-1171c,1172c-1172f,1173a-117ff,1183b-1189f,118ea-118fe,11907-11908,1190a-1190b,11914,11917,11936,11939-1193a,11944-1194f,1195a-1199f,119a8-119a9,119d8-119d9,119e2,119e5-119ff,11a3f-11a46,11a48-11a4f,11a9a-11a9c,11a9e-11abf,11af9-11bff,11c09,11c37,11c41-11c4f,11c5a-11c71,11c90-11c91,11ca8,11cb7-11cff,11d07,11d0a,11d37-11d39,11d3b,11d3e,11d48-11d4f,11d5a-11d5f,11d66,11d69,11d8f,11d92,11d99-11d9f,11daa-11edf,11ef7-11faf,11fb1-11fff,1239a-123ff,1246f-1247f,12544-12fff,1342f-143ff,14647-167ff,16a39-16a3f,16a5f,16a6a-16acf,16aee-16aef,16af5-16aff,16b37-16b3f,16b44-16b4f,16b5a-16b62,16b78-16b7c,16b90-16e3f,16e80-16eff,16f4b-16f4e,16f88-16f8e,16fa0-16fdf,16fe2,16fe5-16fef,16ff2-16fff,187f8-187ff,18cd6-18cff,18d09-1afff,1b11f-1b14f,1b153-1b163,1b168-1b16f,1b2fc-1bbff,1bc6b-1bc6f,1bc7d-1bc7f,1bc89-1bc8f,1bc9a-1bc9c,1bc9f-1d164,1d16a-1d16c,1d173-1d17a,1d183-1d184,1d18c-1d1a9,1d1ae-1d241,1d245-1d3ff,1d455,1d49d,1d4a0-1d4a1,1d4a3-1d4a4,1d4a7-1d4a8,1d4ad,1d4ba,1d4bc,1d4c4,1d506,1d50b-1d50c,1d515,1d51d,1d53a,1d53f,1d545,1d547-1d549,1d551,1d6a6-1d6a7,1d6c1,1d6db,1d6fb,1d715,1d735,1d74f,1d76f,1d789,1d7a9,1d7c3,1d7cc-1d7cd,1d800-1d9ff,1da37-1da3a,1da6d-1da74,1da76-1da83,1da85-1da9a,1daa0,1dab0-1dfff,1e007,1e019-1e01a,1e022,1e025,1e02b-1e0ff,1e12d-1e12f,1e13e-1e13f,1e14a-1e14d,1e14f-1e2bf,1e2fa-1e7ff,1e8c5-1e8cf,1e8d7-1e8ff,1e94c-1e94f,1e95a-1edff,1ee04,1ee20,1ee23,1ee25-1ee26,1ee28,1ee33,1ee38,1ee3a,1ee3c-1ee41,1ee43-1ee46,1ee48,1ee4a,1ee4c,1ee50,1ee53,1ee55-1ee56,1ee58,1ee5a,1ee5c,1ee5e,1ee60,1ee63,1ee65-1ee66,1ee6b,1ee73,1ee78,1ee7d,1ee7f,1ee8a,1ee9c-1eea0,1eea4,1eeaa,1eebc-1f12f,1f14a-1f14f,1f16a-1f16f,1f18a-1fbef,1fbfa-1ffff,2a6de-2a6ff,2b735-2b73f,2b81e-2b81f,2cea2-2ceaf,2ebe1-2f7ff,2fa1e-2ffff,3134b-e00ff,e01f0-10ffff"


def _parse_excluded_ranges(spec: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
    starts: list[int] = []
    ends: list[int] = []
    for item in spec.split(","):
        start, separator, end = item.partition("-")
        starts.append(int(start, 16))
        ends.append(int(end, 16) if separator else starts[-1])
    return tuple(starts), tuple(ends)


_EXCLUDED_STARTS, _EXCLUDED_ENDS = _parse_excluded_ranges(_EXCLUDED_RANGE_SPEC)


def _is_excluded(character: str) -> bool:
    codepoint = ord(character)
    index = bisect_right(_EXCLUDED_STARTS, codepoint) - 1
    return index >= 0 and codepoint <= _EXCLUDED_ENDS[index]


def _base_slug(value: str) -> str:
    lowered = value.lower()
    return "".join(
        "-" if character == " " else character
        for character in lowered
        if not _is_excluded(character)
    )


class GithubSlugger:
    """Allocate document-scoped heading slugs using github-slugger 2.0.0."""

    def __init__(self) -> None:
        self._occurrences: dict[str, int] = {}

    def slug(self, value: str) -> str:
        """Return the next collision-free slug for visible heading text."""

        result = _base_slug(value)
        original = result
        while result in self._occurrences:
            self._occurrences[original] += 1
            result = f"{original}-{self._occurrences[original]}"
        self._occurrences[result] = 0
        return result
