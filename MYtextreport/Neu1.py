    def get_one_relationship(self, db, orig_person, other_person, 
                             extra_info=False, olocale=glocale):
        """
        Returns a string representing the most relevant relationship between 
        the two people. If extra_info = True, extra information is returned:
        (relation_string, distance_common_orig, distance_common_other)

        If olocale is passed in (a GrampsLocale) that language will be used.

        :param olocale: allow selection of the relationship language
        :type olocale: a GrampsLocale instance
        """
        self._locale = olocale
        stop = False
        if orig_person is None:
            rel_str = _("undefined")
            stop = True

        if not stop and orig_person.get_handle() == other_person.get_handle():
            rel_str = ''
            stop = True

        if not stop:
            is_spouse = self.is_spouse(db, orig_person, other_person)
            if is_spouse:
                rel_str = is_spouse
                stop = True
        
        if stop:
            if extra_info:
                return (rel_str, -1, -1)
            else:
                return rel_str
        
        data, msg = self.get_relationship_distance_new(
                                db, orig_person, other_person,
                                all_dist=True,
                                all_families=True, only_birth=False)
        if data[0][0] == -1:
            if extra_info:
                return ('', -1, -1)
            else:
                return ''

        data = self.collapse_relations(data)

        #most relevant relationship is a birth family relation of lowest rank
        databest = [data[0]]
        rankbest = data[0][0]
        for rel in data :
            #data is sorted on rank
            if rel[0] == rankbest:
                databest.append(rel)
        rel = databest[0]
        dist_orig = len(rel[2])
        dist_other = len(rel[4])
        if len(databest) == 1:
            birth = self.only_birth(rel[2]) and self.only_birth(rel[4])
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
                                                  rel[2], rel[4],
                                                  only_birth=birth, 
                                                  in_law_a=False, 
                                                  in_law_b=False)
        else:
            order = [self.REL_FAM_BIRTH, self.REL_FAM_BIRTH_MOTH_ONLY,
                     self.REL_FAM_BIRTH_FATH_ONLY, self.REL_MOTHER,
                     self.REL_FATHER, self.REL_SIBLING, self.REL_FAM_NONBIRTH, 
                     self.REL_MOTHER_NOTBIRTH, self.REL_FATHER_NOTBIRTH]
            orderbest = order.index(self.REL_MOTHER)
            for relother in databest:
                relbirth = self.only_birth(rel[2]) and self.only_birth(rel[4])
                if relother[2] == '' or relother[4] == '':
                    #direct relation, take that
                    rel = relother
                    break
                if not relbirth and self.only_birth(relother[2]) \
                                and self.only_birth(relother[4]) :
                    #birth takes precedence
                    rel = relother
                    continue
                if order.index(relother[2][-1]) < order.index(rel[2][-1]) and\
                        order.index(relother[2][-1]) < orderbest:
                    rel = relother
                    continue
                if order.index(relother[4][-1]) < order.index(rel[4][-1]) and\
                        order.index(relother[4][-1]) < orderbest:
                    rel = relother
                    continue
                if order.index(rel[2][-1]) < orderbest or \
                        order.index(rel[4][-1]) < orderbest:
                    #keep the good one
                    continue
                if order.index(relother[2][-1]) < order.index(rel[2][-1]):
                    rel = relother
                    continue
                if order.index(relother[2][-1]) == order.index(rel[2][-1]) and\
                        order.index(relother[4][-1]) < order.index(rel[4][-1]):
                    rel = relother
                    continue
            dist_orig = len(rel[2])
            dist_other = len(rel[4])
            pos_not = self.get_posnot( orig_person, other_person, rel[2], rel[4])
            birth = self.only_birth(rel[2]) and self.only_birth(rel[4])
            if dist_orig == dist_other == 1:
                rel_str =  self.get_sibling_relationship_string(
                            self.get_sibling_type(
                                                db, orig_person, other_person), 
                            orig_person.get_gender(),
                            other_person.get_gender())
            else:
                rel_str = self.get_single_relationship_string(dist_orig,
                                                  dist_other,
                                                  orig_person.get_gender(),
                                                  other_person.get_gender(),
                                                  rel[2], rel[4],
                                                  only_birth=birth, 
                                                  in_law_a=False, 
                                                  in_law_b=False)


            rel_str = rel_str + " | " +pos_not+ " | " +rel[2]+"  "+rel[4]
        if extra_info:
            return (rel_str, dist_orig, dist_other)
        else:
            return rel_str

