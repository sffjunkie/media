# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

from mogul.media import localize
_ = localize()

class IPTCHandler(object):
    def __init__(self):
        self._elements = {
            'City':
                ('photoshop', 'text',
                 'City',
                 _('Name of the city')),
            'Country':
                ('photoshop', 'text',
                 'Country',
                 _('Name of the country')),
            'CountryCode':
                ('Iptc4xmpCore', 'iso3166', 
                 'Country Code',
                 _('ISO 3166 Country Code')),
            'description':
                ('dc', 'langalt',
                 'Description',
                 _('￼A textual description, including captions, of the image.')),
            'Headline':
                ('photoshop', 'text',
                 'Headline',
                 _('￼A brief synopsis of the caption.')),
            'IntellectualGenre':
                ('Iptc4xmpCore', 'text',
                 'Intellectual Genre',
                 _('￼Describes the nature, intellectual, artistic or journalistic characteristic of a item, not specifically its content.')),
            'subject':
                ('dc', 'text',
                 'Keywords',
                 _('￼Keywords to express the subject of the content')),
            'State':
                ('photoshop', 'text',
                 'Province or State',
                 _('￼Name of the subregion of a country')),
            'Scene':
                ('Iptc4xmpCore', 'bag:text',
                 'Scene Code',
                 _('￼Describes the scene of a news content')),
            'SubjectCode':
                ('Iptc4xmpCore', 'bag:text',
                 'Subject Code',
                 _('￼Specifies one or more Subjects from the IPTC Subject-NewsCodes taxonomy to categorise the content')),
            'Location':
                ('Iptc4xmpCore', 'text',
                 'Sublocation',
                 _('Name of a sublocation the content is focussing on')),
            'DateCreated':
                ('photoshop', 'date',
                 'Date Created',
                 _('Designates the date and optionally the time the intellectual content was created rather than the date of the creation of the physical representation.')),
            'CaptionWriter':
                ('photoshop', 'text',
                 'Description Writer',
                 _('￼Identifier or the name of the person involved in writing, editing or correcting the description of the content.')),
            'Instructions':
                ('photoshop', 'text',
                 'Instructions',
                 _('Any of a number of instructions from the provider or creator to the receiver of the item.')),
            'TransmissionReference':
                ('photoshop', 'text',
                 'Job Id',
                 _('Number or identifier for the purpose of improved workflow handling.')),
            'title':
                ('dc', 'langalt',
                 'Title',
                 _('A shorthand reference for the item. Title provides a short human readable name which can be a text and/or numeric reference. It is not the same as Headline.')),
            'rights':
                ('dc', 'langalt',
                 'Copyright Notice',
                 _('Contains any necessary copyright notice for claiming the intellectual property for this item and should identify the current owner of the copyright for the item. Other entities like the creator of the item may be added in the corresponding field. Notes on usage rights should be provided in "Rights usage terms".')),
            'creator':
                ('dc', 'seq:propername',
                 'Creator',
                 _('Contains the name of the person who created the content of this item, a photographer for photos, a graphic artist for graphics, or a writer for textual news, but in cases where the photographer should not be identified the name of a company or organisation may be appropriate.')),
            'CreatorContactInfo':
                ('Iptc4xmpCore', 'contactinfo',
                 "Creator's Contact Info",
                 _("The creator's contact information provides all necessary information to get in contact with the creator of this item and comprises a set of sub-properties for proper addressing.")),
            'AuthorsPosition':
                ('photoshop', 'text',
                 "Creator's Jobtitle",
                 _("Contains the job title of the person who created the content of this item. As this is sort of a qualifier the Creator element has to be filled in as mandatory prerequisite for using Creator's Jobtitle.")),
            'Credit':
                ('photoshop', 'text',
                 'Credit Line',
                 _('The credit to person(s) and/or organisation(s) required by the supplier of the item to be used when published.')),
            'UsageTerms':
                ('xmpRights', 'langalt',
                 'Rights Usage Terms',
                 _('The licensing parameters of the item expressed in free-text.')),
            'Source':
                ('photoshop', 'text',
                 'Source',
                 _('Identifies the original owner of the copyright for the intellectual content of the image. This could be an agency, a member of an agency or an individual. Source could be different from Creator and from the entities in the CopyrightNotice.')),
            'ContactInfoDetails':
                ('Iptc4xmpCore', 'structure',
                 'Contact Information Details structure {data type}',
                 _('A generic structure providing a basic set of information to get in contact with a person or organisation. It includes an Address, a City, a Country, Email address, Phone number, a Postal Code, a State or Province and Web URL.')),
            'CiAdrExtadr':
                ('Iptc4xmpCore', 'text',
                 'Address {contact metadata detail}',
                 _('The contact information address part. Comprises an optional company name and all required information to locate the building or postbox to which mail should be sent. To that end, the address is a multiline field.')),
            'CiAdrCity':
                ('Iptc4xmpCore', 'text',
                 'City {contact metadata detail}',
                 _('The contact information city part.')),
            'CiAdrCtry':
                ('Iptc4xmpCore', 'text',
                 'Country {contact metadata detail}',
                 _('The contact information country part.')),
            'CiEmailWork':
                ('Iptc4xmpCore', 'text',
                 'Email address(es) {contact metadata detail}',
                 _('The contact information email address part.')),
            'CiTelWork':
                ('Iptc4xmpCore', 'text',
                 'Phone number(s) {contact metadata detail}',
                 _('The contact information phone number part.')),
            'CiAdrPcode':
                ('Iptc4xmpCore', 'text',
                 'Postal Code {contact metadata detail}',
                 _('The contact information part denoting the local postal code.')),
            'CiAdrRegion':
                ('Iptc4xmpCore', 'text',
                 'State/Province {contact metadata detail}',
                 _('The contact information part denoting regional information such as state or province.')),
            'CiUrlWork':
                ('Iptc4xmpCore', 'text',
                 'Web URL(s) {contact metadata detail}',
                 _('The contact information web address part. Multiple addresses can be given, separated by a comma.')),
            'AddlModelInfo':
                ('Iptc4xmpExt', 'text',
                 'Additional Model Information',
                 _('Information about the ethnicity and other facets of the model(s) in a model-released image.')),
            'ArtworkOrObject':
                ('Iptc4xmpExt', '￼bag:ArtworkOrObjectDetails',
                 'Artwork or Object in the Image',
                 _('A set of metadata about artwork or an object in the image.')),
            'OrganisationInImageCode':
                ('Iptc4xmpExt', '￼bag:text',
                 'Code of Organisation Featured in the Image',
                 _('Code from a controlled vocabulary for identifying the organisation or company which is featured in the content.')),
            'CVterm':
                ('Iptc4xmpExt', '￼bag:uri',
                 'Controlled Vocabulary Term',
                 _('A term to describe the content of the image by a value from a Controlled Vocabulary.')),
            'LocationShown':
                ('Iptc4xmpExt', '￼bag:LocationDetails',
                 'Location Shown in the Image',
                 _('A location the content of the item is about. For photos that is a location shown in the image.')),
            'ModelAge':
                ('Iptc4xmpExt', '￼bag:integer',
                 'Model Age',
                 _('Age of the human model(s) at the time this image was taken in a model released image.')),
            'OrganisationInImageName':
                ('Iptc4xmpExt', '￼bag:text',
                 'Name of Organisation Featured in the Image',
                 _('Name of the organisation or company which is featured in the content.')),
            'PersonInImage':
                ('Iptc4xmpExt', '￼bag:text',
                 'Person Shown in the Image',
                 _('Name of a person the content of the item is about. For photos that is a person shown in the image.')),
            'DigImageGUID':
                ('Iptc4xmpExt', '￼text',
                 'Digital Image GUID',
                 _('Globally unique identifier for the item. It is created and applied by the creator of the item at the time of its creation . This value shall not be changed after that time.')),
            'Event':
                ('Iptc4xmpExt', '￼langalt',
                 'Event',
                 _('Names or describes the specific event the content relates to.')),
            'RegistryId':
                ('Iptc4xmpExt', 'bag:RegistryEntryDetails',
                 'Image Registry Entry',
                 _('Both a Registry Item Id and a Registry Organisation Id to record any registration of this item with a registry.')),
            'ImageSupplier':
                ('Iptc4xmpExt', 'seq:ImageSupplierDetail',
                 'Image Supplier',
                 _('Identifies the most recent supplier of the item, who is not necessarily its owner or creator.')),
            'ImageSupplierImageID':
                ('plus', 'text',
                 'Image Supplier Image ID',
                 _('Optional identifier assigned by the Image Supplier to the image.')),
            'IptcLastEdited':
                ('Iptc4xmpExt', 'date',
                 'IPTC Metadata Last Edited (Legacy)',
                 _('The date and optionally time when any of the IPTC edited.')),
            'LocationCreated':
                ('Iptc4xmpExt', 'bag:LocationDetails',
                 'Location created',
                 _('The location the content of the item was created.')),
            'MaxAvailHeight':
                ('Iptc4xmpExt', 'integer',
                 'Max Avail Height',
                 _('The maximum available height in pixels of the original photo from which this photo has been derived by downsizing.')),
            'MaxAvailWidth':
                ('Iptc4xmpExt', 'integer',
                 'Max Avail Width',
                 _('The maximum available width in pixels of the original photo from which this photo has been derived by downsizing.')),
            'Version':
                ('plus', 'text',
                 'PLUS Version',
                 _('The version number of the PLUS standards in place at the time of the transaction.')),
            'CopyrightOwner':
                ('plus', 'seq:CopyrightOwnerDetail',
                 'Copyright Owner',
                 _('Owner or owners of the copyright in the licensed image.')),
            'ImageCreator':
                ('plus', 'seq:ImageCreatorDetail',
                 'Image Creator',
                 _('Creator or creators of the image.')),
            'Licensor':
                ('plus', 'bag:LicensorDetail',
                 'Licensor',
                 _('A person or company that should be contacted to obtain a licence for using the item or who has licensed the item.')),
            'MinorModelAgeDisclosure':
                ('plus', 'url',
                 'Minor Model Age Disclosure',
                 _('Age of the youngest model pictured in the image, at the time that the image was made.')),
            'ModelReleaseID':
                ('plus', 'bag:text',
                 'Model Release Id',
                 _('Optional identifier associated with each Model Release.')),
            'ModelReleaseStatus':
                ('plus', 'url',
                 'Model Release Status',
                 _('Summarizes the availability and scope of model releases authorizing usage of the likenesses of persons appearing in the photograph.')),
            'PropertyReleaseID':
                ('plus', 'bag:text',
                 'Property Release Id',
                 _('Optional identifier associated with each Property Release.')),
            'PropertyReleaseStatus':
                ('plus', 'url',
                 'Property Release Status',
                 _('Summarises the availability and scope of property releases authorizing usage of the properties appearing in the photograph.')),
        }
        
        self.metadata = {}
        
        self._ns = ('iptc', 'http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/')
        self._ns_photoshop = ('photoshop', 'http://ns.adobe.com/photoshop/1.0/')
        self._ns_dublincore = ('dc', 'http://purl.org/dc/elements/1.1/')
