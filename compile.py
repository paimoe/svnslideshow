import argparse
import os
import json

verbose = False

def vb(msg):
    if verbose:
        print msg
        
def parse_hunk_delim(delim):
    """
    Parse @@ -40,15 +40,27 @@
    """
    sp = delim.split(' ')
    del(sp[0])
    del(sp[-1]) # delete first and last
    
    original = sp[0].split(',')
    updated = sp[1].split(',')
    
    result = {
        'o_start': int(original[0][1:]),
        'o_changed': int(original[1]),
        'u_start': int(updated[0][1:]),
        'u_changed': int(updated[1])
    }
    return result

def compilepatch(single=None):
    """
    
    """
    #
    result = {}
    revnum = 1
    
    # Get which files we're compiling
    filelist = []
    if single is not None:
        # Check exists
        if single.endswith('.patch') is False:
            single += '.patch'
        filelist.append(single)
    else:        
        for root, dirs, files in os.walk('.'):
            for f in files:
                if f.endswith('.patch'): 
                    filelist.append(f)
    
    # Get original source file, so I can compare hunks to see if they're changed, removed, added
    
    # Loop files, open, compile, uh close
    for patch in filelist:
        vb('Parsing %s' % patch)
        
        hunks = []
        in_hunk = 0
        rev = patch[1:-6] # r184.patch, gets 184
        vb(rev)
        
        blocks = [] # each changed line, with the changed result
        
        with open(patch, 'r') as f:
            diff = f.readlines()
            
            previous_line_addition = False
            previous_line_remove = False
            for line in diff:
                if line.startswith('@@'):
                    hunk = parse_hunk_delim(line)
                    # diff hunk
                    in_hunk += 1
                    in_hunk_start = hunk['o_start'] - 1 # parse @@ line
                    vb('in_hunk_start: %s' % in_hunk_start)
                    continue
                if in_hunk > 0:
                    # Check if this line is blank, or new, or removed
                    revset = {}
                    in_hunk_start += 1
                    if line == '':
                        previous_line_addition = False
                        previous_line_remove = False
                    elif line.startswith('+'):
                        # Line was added
                        revset['line'] = in_hunk_start
                        
                        # If we previously removed a line, and now we're adding, then merge the two
                        if previous_line_remove:
                            # Remove previous instruction
                            vb('Removing previous instruction')
                            blocks.pop()
                            revset['replaceWith'] = line[1:]
                            revset['line'] = in_hunk_start
                        
                        if previous_line_addition: # If we added on the previous line
                            revset['addAfter'] = line[1:]
                            revset['line'] = in_hunk_start - 1 # I guess it makes sense. We're adding ON line 200, but AFTER line 199
                        else:
                            revset['replaceWith'] = line[1:] # cleanup, but whatever
                            previous_line_addition = True
                        
                        previous_line_remove = False
                    elif line.startswith('-'):
                        # Line was removed
                        revset['line'] = in_hunk_start # change this var name
                        revset['removeLine'] = True
                        previous_line_addition = False
                        previous_line_remove = True
                        in_hunk_start -= 1
                    else:
                        previous_line_remove = False
                        continue # skip lines that are unchanged
                    
                    # Append to revisions
                    if len(revset) > 0: # skip blank lines
                        blocks.append(revset)
                    
        result[rev] = blocks
    import pprint
    print pprint.pprint(result)
    
    # Save off revs 
    with open('compiled.js', 'w') as jsfile:
        jsfile.write(json.dumps(result))

if __name__ == '__main__':    
    parser = argparse.ArgumentParser(description='Compile SVN diffs')
    parser.add_argument('-p', '--patch', help='Specify single revision to compile, instead of all')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    opts = parser.parse_args()
    
    if opts.verbose:
        verbose = True
    
    compilepatch(opts.patch)
