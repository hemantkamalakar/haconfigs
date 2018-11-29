from locationsharinglib import Service
service = Service("pranav.kamalakar@gmail.com", "Soham2018", cookies_file=".google_maps_location_sharing.cookies")
for person in service.get_all_people():
    print(person)
