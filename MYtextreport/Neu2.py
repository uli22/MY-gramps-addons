    def get_all_relationships(self, db, orig_person, other_person):
        """
        Return a tuple, of which the first entry is a list with all
        relationships in text, and the second a list of lists of all common
        ancestors that have that text as relationship
        """
        relstrings = []
        commons = {}
        if orig_person is None:
            return ([], [])

        if orig_person.get_handle() == other_person.get_handle():
            return ([], [])

        is_spouse = self.is_spouse(db, orig_person, other_person)
        if is_spouse:
            relstrings.append(is_spouse)
            commons[is_spouse] = []
        
        data, msg = self.get_relationship_distance_new(
                                db, orig_person, other_person,
                                all_dist=True,
                                all_families=True, only_birth=False)
        if not data[0][0] == -1:
            data = self.collapse_relations(data)
            for rel in data :
                rel2 = rel[2]
                rel4 = rel[4]
                rel1 = rel[1]
                dist_orig = len(rel[2])
                dist_other = len(rel[4])
                if rel[2] and rel[2][-1] == self.REL_SIBLING:
                    rel2 = rel2[:-1] + self.REL_FAM_BIRTH
                    dist_other += 1
                    rel4 = rel4 + self.REL_FAM_BIRTH
                    rel1 = None
                birth = self.only_birth(rel2) and self.only_birth(rel4)
                if dist_orig == dist_other == 1:
                    rel_str = self.get_sibling_relationship_string(
                                self.get_sibling_type(
                                                db, orig_person, other_person), 
                                orig_person.get_gender(),
                                other_person.get_gender())
                else:
                    rel_str = self.get_single_relationship_string(dist_orig,
                                                     dist_other,
                                                     orig_person.get_gender(),
                                                     other_person.get_gender(),
                                                     rel2, rel4,
                                                     only_birth=birth, 
                                                     in_law_a=False, 
                                                     in_law_b=False)
                if not rel_str in relstrings:
                    relstrings.append(rel_str)
                    if rel1:
                        commons[rel_str] = rel1
                    else:
                        #unknown parent eg
                        commons[rel_str] = []
                else:
                    if rel1:
                        commons[rel_str].extend(rel1)
        #construct the return tupply, relstrings is ordered on rank automatic
        common_list = []
        for rel_str in relstrings:
            common_list.append(commons[rel_str])
        return (relstrings, common_list)
