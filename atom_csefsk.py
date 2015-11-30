'''This is the Homework2 of CS6233 SectionB, offered by prof. Katz
The program is a file system checker, called "csefsk". It is used to check the following things:
1) DeviceID is correct
2) All times are in the past, nothing in the future
3) Validate that the free block list is accurate:
    a) make sure the free block list contains ALL of the free blocks
    b) make sure that there are no files/directories stored on items listed in the free block list
4) Each directory contains . and .. and their block numbers are correct
5) Each directory's link count matches the number of links in the filename_to_inode_dict
6) If the data contained in a location pointer is an array, that indirect is one
7) The size is valid for the number of block pointers in the location array. There are three possibilities:
    a) size < blocksize if indirect = 0 & size > 0
    b) size < (blocksize * length of location array) if indirect != 0
    c) size > (blocksize * (length of location array - 1)) if indirect != 0
'''


from time import time
freestart = 1
freeend = 25
DEVID = 20
ROOT_BLOCK = '26'
MAX_BLOCK_NUM = 10000
blocksize = 4096
current_time = int(time())
root_path = 'FS/fusedata.26'
superblock_path = 'FS/fusedata.0'
used_block_list = [ROOT_BLOCK]
file_data_block_list = []
free_block_list = []
free_temp_list = []

# Store free blocks into a list
def free_block_search():
    for i in range(freestart,freeend+1):
        f = open('FS/fusedata.' + str(i), 'r')
        Temp_str = f.read()
        Temp_list = strtransfer(Temp_str)
        for j in Temp_list:
            free_block_list.append(j)
        f.close()

def strtransfer(string):
    content = string.split(',')
    for i in range(len(content)):
        content[i] = content[i].strip()
    return content

# Check whether DevID is right
def DevID_check(file_path):
    file = open(file_path,'r')
    content = file.read()
    file.close()
    devID_startindex = content.find('devId')
    devID = int(content[devID_startindex+6:devID_startindex+8])
    if devID != DEVID:
        print '***The devID for the file system is wrong. It shoule be %d'%(DEVID)
    #else:
        #print 'The devID is right!'

# Check time, if time is later than current time, change it to the current time
def time_check(block_number):
    file = open('FS/fusedata.%s'%(block_number),'r')
    changed = False
    content = file.read()
    file.close()
    atime_startindex = content.find('atime:')
    atime_stopindex = content[atime_startindex:].find(',') + atime_startindex
    atime = content[atime_startindex+6:atime_stopindex]
    ctime_startindex = content.find('ctime:')
    ctime_stopindex = content[ctime_startindex:].find(',') + ctime_startindex
    ctime = content[ctime_startindex+6:ctime_stopindex]
    mtime_startindex = content.find('mtime:')
    mtime_stopindex = content[mtime_startindex:].find(',') + mtime_startindex
    mtime = content[mtime_startindex+6:mtime_stopindex]
    if int(atime) > current_time:
        changed = True
        print '***The atime of block %s is wrong, changed it to current time!'%(block_number)
        atime = str(current_time)
    if int(ctime) > current_time:
        changed = True
        print '***The ctime of block %s is wrong, changed it to current time!'%(block_number)
        ctime = str(current_time)
    if int(mtime) > current_time:
        changed = True
        print '***The mtime of block %s is wrong, changed it to current time!'%(block_number)
        mtime = str(current_time)
    if changed == True:
        new_str = content[:atime_startindex]+'atime:%s'%(atime)+content[atime_stopindex:ctime_startindex]+'ctime:%s'%(ctime)+content[ctime_stopindex:mtime_startindex]+'mtime:%s'%(mtime)+content[mtime_stopindex:]
        new_file = open('FS/fusedata.%s'%(block_number),'w+')
        new_file.write(new_str)

#Started from root block, detect the used blocks
def root_check(file_path):
    file = open(file_path,'r+')
    content = file.read()
    file.close()
    #currentdir_target_block,parentdir_target_block = directory_current_parent(content, ROOT_BLOCK)
        #if currentdir_target_block != ROOT_BLOCK:
        #print '***The . and .. directory of root is wrong. They should be the root_block itself'
        #if parentdir_target_block != ROOT_BLOCK:
    detect_directory(content, ROOT_BLOCK,ROOT_BLOCK)
    detect_file(content,ROOT_BLOCK)

#Check if the directory has . and .. , if no, print cautions
def directory_current_parent(content,block_num):
    currentdir_startindex = content.find('d:.:')
    if currentdir_startindex < 0 :
        print '***The directory block %s has no . !'%(block_num)
    currentdir_stopindex = content[currentdir_startindex:].find(',') + currentdir_startindex
    currentdir_target_block = content[currentdir_startindex+4:currentdir_stopindex]

    parentdir_startindex = content.find('d:..:')
    if parentdir_startindex < 0 :
        print '***The directory block %s has no .. !'%(block_num)
    parentdir_stopindex = content[parentdir_startindex:].find(',') + parentdir_startindex
    parentdir_target_block = content[parentdir_startindex+5:parentdir_stopindex]

    return currentdir_target_block, parentdir_target_block

#Check dicrectory, detect used block and store it into used_block_list. If the block nnumber of . and .. is wrong, print cautions.
def detect_directory(content,current_block,parent_block):
    directory_current_parent(content,current_block)
    linkcount_check(content, current_block)
    start = content.find('{d:')
    if start < 0:
        start = content.find(' d:')
    next = start
    while next > 0:
            temp_end = content[start:].find(',')
            if temp_end >0:
                end = content[start:].find(',') + start
            else:
                end = content[start:].find('}') + start
            if content[start+3:start+5] == '..':
                block_num = content[start+6:end]
                if block_num != parent_block:
                    print '***Block %s has a wrong .. block, which should be %s' %(current_block,parent_block)
            elif content[start+3:start+5] == '.:':
                block_num = content[start+5:end]
                if block_num != current_block:
                    print '***Block %s has a wrong . block, which should be %s' %(current_block,current_block)
            else:
                block_start = content[start+3:].find(':') + start+3
                block_num = content[block_start+1:end]
                if block_num not in used_block_list and int(block_num)>25:
                    used_block_list.append(block_num)
                new_file = open('FS/fusedata.%s'%(block_num),'r')
                new_content = new_file.read()
                new_file.close()
                detect_directory(new_content,block_num,current_block)
                detect_file(new_content,block_num)
            next = content[end:].find(' d:')
            start = content[end:].find(' d:') + end

#Check if each directory's link count matches the number of links in the filename_to_inode_dict.
def linkcount_check(content,current_block):
    linkcount_start = content.find('linkcount:')
    linkcount_end = content[linkcount_start:].find(',') + linkcount_start
    linkcount = content[linkcount_start+10:linkcount_end]
    filename_start = content.find('dict: {')
    all_files = content[filename_start:].split(',')
    files_count = len(all_files)
    if files_count != int(linkcount):
        print "***The linkcount of directory block %s doesn't match the number of links! Which should be %d, not %s"%(current_block, files_count, linkcount)


#Check file inode, detect used block and store it into used_block_list, check the indirect number and size.
def detect_file(content,current_block):
    start = content.find('f:')
    next=start
    while next > 0:
        end = content[start:].find(',') + start
        block_start = content[start+2:].find(':') + start + 2
        block_num = content[block_start+1:end]
        if block_num not in used_block_list:
            used_block_list.append(block_num)
            new_file = open('FS/fusedata.%s'%(block_num),'r')
            new_content = new_file.read()
            new_file.close()
            detect_filelocation(new_content)
            indirect_check(new_content,block_num)
        next = content[end:].find('f:')
        start = content[end:].find('f:') + end

# Detect the location of file, and store the block into used_block_list, and check the block size.
def detect_filelocation(content):
    start = content.find('location:')
    end = content[start:].find('}') + start
    location_num = content[start+9:end]
    used_block_list.append(location_num)
    file_data_block_list.append(location_num)

#Check the indirect number, if the location pointer is an array, indirect should be 1; else, indirect should be 0. If indirect is right, check the size of the file.
def indirect_check(content,current_block):
    indirect_start = content.find('indirect:')
    indirect = content[indirect_start+9]
    location_start = content.find('location:')
    location_part = content[location_start:]
    location_num = len(location_part.split(','))
    if int(indirect) > 1:
        print "***The inode block %s has an undefied indirect, which should be 1 or 0."
        return
    if location_num > 1 and int(indirect) == 0:
        print "***The inode block %s has a wrong indirect, which should be 1, because the location pointer is an array!"%(current_block)
        return
    if location_num == 1 and int(indirect) == 1:
        print "***The inode block %s has a wrong indirect, which should be 0, because the location pointer is one block number!"%(current_block)
        return
    size_check(content,current_block,indirect,location_num)



#Check size of a inode block.
def size_check(content,current_block, indirect, location_num):
    size_end = content.find(',')
    size = int(content[6:size_end])
    if int(indirect) == 0:
        if size > blocksize or size < 0:
            print "***The inode block %s has a wrong size, since the indirect is 0, size should between 0 and 4096."%(current_block)
    else:
        if size > blocksize * location_num or size < blocksize * (location_num-1):
            print "***The inode block %s has a wrong size, since the indirect is 1, size should between 4096*(length of location array) and 4096*(length of location array-1)."%(current_block)




#Check if free blocks are all shown in the 1-25 blocks, if no, print cautions. Check if there are used blocks in free block list, if no, show cautions.
def free_used_check(free_block_list,used_block_list):
    for i in used_block_list:
        if i in free_block_list:
            print '***Block %s is used!!! It is not free!!'%(i)
    all_blocks = ['%s'%(str(i)) for i in range(26, MAX_BLOCK_NUM)]
    Actual_free_blocks = list(set(all_blocks).difference(set(used_block_list)))
    Missed_free_blocks = list(set(Actual_free_blocks).difference(set(free_block_list)))
    if Missed_free_blocks != []:
        print "***These blocks are actually free, but they didn't show in the free block list: " + ", ".join(Missed_free_blocks)




def main():
    DevID_check(superblock_path) #Check if DevID = 20
    free_block_search()  #Go through the free block list, and store them into a list seperately
    root_check(root_path) # Start from root block, search for all the used blocks, and store them into used_block_list. Each time get into a directory or file inode, check the things including . & .. , linkcount, indirect etc.
    free_used_check(free_block_list,used_block_list) #Check if blocks in free list are all free, if there are missing blocks
    blocks_with_time = list(set(used_block_list).difference(set(file_data_block_list)))#Find out the used blocks with time attribute, then do time check
    for i in blocks_with_time:
        time_check(i)


if __name__ == '__main__':
    main()
