from datetime import datetime

def wm_time(s):
    return datetime.strptime(s, '%d/%m/%Y %H:%M:%S')

def wm_time_ordinal(s):
    return int(s)

def wm_time_year_month(s):
    return datetime.strptime(s, '%m/%Y')

def wm_time_year_month_day(s):
    return datetime.strptime(s, '%d/%m/%Y')

tag_targets_mapping = {
    'Abstract': (30, 'SYNOPSIS'),
    'AcquisitionTime': (30, wm_time),
    'Copyright': (30, 'COPYRIGHT'),
    'Description': (30, 'DESCRIPTION'),
    'WM/AlbumArtist': (50, 'ARTIST'),
    'WM/AlbumTitle': (50, 'TITLE'),
    'WM/Composer': (30, 'COMPOSER'),
    'WM/Conductor': (30, 'CONDUCTOR'),
    'WM/Director': (30, 'DIRECTOR'),
    'WM/EncodingTime': (30, 'DATE_ENCODED'),
    'WM/GenreID': (30, 'GENRE'),
    'WM/InitialKey': (30, 'INITIAL_KEY'),
    'WM/Lyrics': (30, 'LYRICS'),
    'WM/MCDI': (30, 'MCDI'),
    'WM/Mood': (30, 'MOOD'),
    'WM/OriginalAlbumTitle': (50, ('ORIGINAL', 'TITLE')),
    'WM/OriginalArtist': (30, ('ORIGINAL', 'ARTIST')),
    'WM/OriginalLyricist': (30, ('ORIGINAL', 'LYRICIST')),
    'WM/ParentalRating': (30, 'LAW_RATING'),
    'WM/PartOfSet': (30, ('PART_NUMBER/TOTAL_PARTS')),
    'WM/Producer': (30, 'PRODUCER'),
    'WM/Publisher': (30, 'PUBLISHER'),
    'WM/SubTitle': (30, 'SUBTITLE'),
    'WM/Track': (30, 'PART_NUMBER'),
    'WM/TrackNumber': (30, 'PART_NUMBER'),
    'WM/WMContentID': (30, 'UID'),
    'WM/UniqueFileIdentifier': 'container.uid',
    'WM/Writer': (30, 'LYRICIST'),
    'WM/Year': (30, 'DATE_RECORDED'),
}

a = """
 Attribute
 Attribute
 Attribute
AcquisitionTimeMonth Attribute
AcquisitionTimeYear Attribute
AcquisitionTimeYearMonth Attribute
AcquisitionTimeYearMonthDay Attribute
AlbumArtistSortOrder Attribute
AlbumID Attribute
AlbumIDAlbumArtist Attribute
AlbumTitleSortOrder Attribute
AlternateSourceURL
AudioBitrate Attribute
AudioFormat Attribute
Author Attribute
AuthorSortOrder Attribute
AverageLevel Attribute
Bitrate Attribute
BuyNow Attribute
BuyTickets Attribute
CallLetters Attribute
CameraManufacturer Attribute
CameraModel Attribute
CDTrackEnabled Attribute
Channels Attribute
chapterNum Attribute
Comment Attribute
ContentDistributorDuration Attribute
 Attribute
Count Attribute
CurrentBitrate Attribute
 Attribute
DisplayArtist Attribute
DLNAServerUDN
DLNASourceURI Attribute
DRMIndividualizedVersion Attribute
DRMKeyID Attribute
DTCPIPHost
DTCPIPPort
Duration Attribute
DVDID Attribute
Event Attribute
FileSize Attribute
FileType Attribute
FormatTag Attribute
FourCC Attribute
FrameRate Attribute
Frequency Attribute
IsNetworkFeed Attribute
IsVBR Attribute
LeadPerformer Attribute
LibraryID
LibraryName Attribute
Location Attribute
MediaType Attribute
ModifiedBy Attribute
MoreInfo Attribute
PartOfSet Attribute
PeakValue Attribute
PixelAspectRatioX Attribute
PixelAspectRatioY Attribute
PlaylistIndex Attribute
Provider Attribute
ProviderLogoURL Attribute
ProviderURL Attribute
RadioBand Attribute
RadioFormat Attribute
RatingOrg Attribute
RecordingTime Attribute
RecordingTimeDay Attribute
RecordingTimeMonth Attribute
RecordingTimeYear Attribute
RecordingTimeYearMonth Attribute
RecordingTimeYearMonthDay Attribute
ReleaseDate Attribute
ReleaseDateDay Attribute
ReleaseDateMonth Attribute
ReleaseDateYear Attribute
ReleaseDateYearMonth Attribute
ReleaseDateYearMonthDay Attribute
RequestState Attribute
ShadowFilePath Attribute
SourceURL Attribute
Subject Attribute
SyncState Attribute
Sync01. See Sync Attributes.
Sync02. See Sync Attributes.
Sync03. See Sync Attributes.
Sync04. See Sync Attributes.
Sync05. See Sync Attributes.
Sync06. See Sync Attributes.
Sync07. See Sync Attributes.
Sync08. See Sync Attributes.
Sync09. See Sync Attributes.
Sync10. See Sync Attributes.
Sync11. See Sync Attributes.
Sync12. See Sync Attributes.
Sync13. See Sync Attributes.
Sync14. See Sync Attributes.
Sync15. See Sync Attributes.
Sync16. See Sync Attributes.
SyncOnly Attribute
Temporary Attribute
Title Attribute
titleNum Attribute
TitleSortOrder Attribute
TotalDuration Attribute
TrackingID Attribute
UserCustom1 Attribute
UserCustom2 Attribute
UserEffectiveRating Attribute
UserLastPlayedTime Attribute
UserPlayCount Attribute
UserPlaycountAfternoon Attribute
UserPlaycountEvening Attribute
UserPlaycountMorning Attribute
UserPlaycountNight Attribute
UserPlaycountWeekday Attribute
UserPlaycountWeekend Attribute
UserRating Attribute
UserServiceRating Attribute
VideoBitrate Attribute
VideoFormat Attribute
WM/Category Attribute
 Attribute
 Attribute
WM/ContentDistributor Attribute
WM/ContentDistributorType Attribute
WM/ContentGroupDescription Attribute
 Attribute
 Attribute
WM/Genre Attribute
 Attribute
 Attribute
WM/Language Attribute
 Attribute
 Attribute
WM/MediaClassPrimaryID Attribute
WM/MediaClassSecondaryID Attribute
WM/MediaOriginalBroadcastDateTime Attribute
WM/MediaOriginalChannel Attribute
WM/MediaStationName Attribute
 Attribute
 Attribute
 Attribute
 Attribute
 Attribute
 Attribute
WM/Period Attribute
 Attribute
WM/ProtectionType Attribute
WM/Provider Attribute
WM/ProviderRating Attribute
WM/ProviderStyle Attribute
 Attribute
WM/SubscriptionContentID Attribute
 Attribute
WM/SubTitleDescription Attribute
 Attribute
WM/UniqueFileIdentifier Attribute
WM/VideoFrameRate Attribute
WM/VideoHeight Attribute
WM/VideoWidth Attribute
WM/WMCollectionGroupID Attribute
WM/WMCollectionID Attribute
 Attribute
 Attribute
 Attribute
"""