from itertools import groupby

from location.gps import GPS

class MediaGroups:

    class Group:

        gps : GPS
        media_keys : list[str]

        def __init__(self : 'MediaGroups.Group', gps : GPS, keys : list[str]) -> 'MediaGroups.Group':
            self.gps = gps
            self.media_keys = keys

        def toDict(self : 'MediaGroups.Group') -> dict:
            return {
                'gps' : self.gps.toDict(),
                'media_keys' : self.media_keys
            }
        
        @classmethod
        def fromDict(cls : 'MediaGroups.Group', d : dict) -> 'MediaGroups.Group':
            gps = GPS.fromDict(d['gps'])
            media_keys = d['media_keys']
            return MediaGroups.Group(
                gps, 
                media_keys,
            )

        """
        def toJSON(self : 'MediaGroups.Group') -> str:
            return json.dumps(self.toDict(), default = lambda o: o.__dict__, indent = 2)
        """
      
    grouping_threshold : float              # threshold distance to group media locations expressed in km
    groups : list['MediaGroups.Group']    # list of gps coordinates representing groups

    def __init__(self : 'MediaGroups', grouping_threshold : float, groups : list['MediaGroups.Group'] = []) -> 'MediaGroups':
        self.grouping_threshold = grouping_threshold
        self.groups = groups

    def toDict(self : 'MediaGroups') -> dict:
        return {
            'grouping_threshold' : self.grouping_threshold,
            'groups' : [self.groups[i].toDict() for i in range(len(self.groups))],
        }
    
    @classmethod
    def fromDict(cls : 'MediaGroups', d : dict) -> 'MediaGroups':
        return MediaGroups(
            grouping_threshold = d['grouping_threshold'], 
            groups = [MediaGroups.Group.fromDict(group) for group in d['groups']],
        )

    def add_locations(self : 'MediaGroups', locations : dict[str, dict]) -> None:      
        for location_key, location_desc in locations.items():
            location_gps = GPS(location_desc['gps']['latitude'], location_desc['gps']['longitude'])

            groups_found = [i for i in range(len(self.groups)) if self.groups[i].gps.distance_to(location_gps) < self.grouping_threshold]

            if groups_found:
                for i in groups_found:
                    barycenter = self.groups[i].gps.barycenter_to(location_gps, len(self.groups[i].media_keys))
                    media_keys = self.groups[i].media_keys.copy()
                    media_keys.append(location_key)

                    del self.groups[i]

                    self.groups.append(MediaGroups.Group(barycenter, media_keys))
            else:
                self.groups.append(MediaGroups.Group(location_gps, [location_key]))

    def get_groups_gps(self : 'MediaGroups') -> list['MediaGroups.Group']:
        return [group.gps for group in self.groups] if self.groups else []
