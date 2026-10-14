import re

tex = open('sqam_paper.tex', encoding='utf-8').read()
bib = open('references.bib', encoding='utf-8').read()

print('=== 1. Undefined Reference & Citation Check ===')
labels = set(re.findall(r'\\label\{([^}]+)\}', tex))
refs = set(re.findall(r'\\(?:ref|eqref)\{([^}]+)\}', tex))
missing_refs = refs - labels
print('Missing labels referenced:', missing_refs)

cites = set()
for c in re.findall(r'\\cite\{([^}]+)\}', tex):
    for s in c.split(','):
        cites.add(s.strip())
bib_keys = set(re.findall(r'@\w+\{([^,]+),', bib))
print('Missing citations:', cites - bib_keys)

print('\n=== 2. Code Fence Check ===')
print('Triple backtick count:', tex.count(chr(96)*3))

print('\n=== 3. Algorithm & Taxonomy Grep ===')
print('Levenshtein count:', len(re.findall(r'levenshtein', tex, re.I)))
print('Six categories count:', len(re.findall(r'six (?:mutually exclusive|categories)', tex, re.I)))
print('Nine categories mentioned:', 'nine' in tex.lower())

print('\n=== 4. Test Count & Numbers Check ===')
print('26 unit tests mentioned:', len(re.findall(r'26\s+unit tests|26\s+test', tex, re.I)))
print('22 unit tests count (should be 0):', len(re.findall(r'22\s+unit tests|22\s+test', tex, re.I)))

print('\n=== 5. Overclaim Words Check ===')
for word in ['proves', 'guarantees', 'completely eliminates', 'completely solves', 'perfectly preserves', 'completely neutralizes', 'completely insulates']:
    print(f'Count of "{word}":', len(re.findall(rf'\b{word}\b', tex, re.I)))

print('\n=== 6. Version Indexing Check ===')
v_final_plus1 = len(re.findall(r'V_\{N\+1\}|V_\{final\}', tex))
v_final_sub1 = len(re.findall(r'V_\{N-1\}', tex))
print('V_{N+1} / V_{final} count:', v_final_plus1)
print('V_{N-1} count (should be 0):', v_final_sub1)

print('\n=== 7. Table 1 Version Sum Check ===')
# IDs 1 to 15 versions: 2+2+5+5+2+6+2+3+2+2+2+2+2+3+3 = 43
versions = [2, 2, 5, 5, 2, 6, 2, 3, 2, 2, 2, 2, 2, 3, 3]
print('Sum of versions:', sum(versions), 'Expected: 43')

print('\n=== ALL CROSS-CHECKS COMPLETE ===')
