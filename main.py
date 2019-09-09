import sys
import xmlrpc.client
import requests
from hash import hashFile
from config import user_agent


def main():

    if (len(sys.argv) < 2):
        print('Error! Pass the path of the video file as an argument.')
        sys.exit(0)

    else:
        # Proxy to the opensubtitles api
        opensubtitles_server_proxy = xmlrpc.client.ServerProxy("http://api.opensubtitles.org/xml-rpc")

        # Login to the server to get the token
        login_details = opensubtitles_server_proxy.LogIn('', '', 'eng', user_agent)
        token = login_details['token']

        # Get the path to the file for which we need the subtitles
        file = sys.argv[1]

        # Get the hash of the video and the size in bytes
        (moviehash, moviebytesize) = hashFile(file)
        
        # Param to search for the subtitles
        movie_details = [
            {
                'sublanguageid': 'eng', 
                'moviehash': moviehash, 
                'moviebytesize': moviebytesize
            }
        ]

        # Search for subtitles 
        subtitle_details = opensubtitles_server_proxy.SearchSubtitles(token, movie_details);
        subs = subtitle_details['data']

        # If more than 1 subtitle is found, prompt user for the choice
        if (len(subs) > 1):
            print('Choose the subtitle: \n')
            for i in range(len(subs)):
                print("%d. %s" % (i+1, subs[i]['SubFileName']))

            choice = input("Enter your choice (%d-%d): " % (1, len(subs))) 
            choice = int(choice)

            if (choice < 1 or choice > len(subs)):
                print('Invalid choice! Exiting')
                sys.exit(0)

        elif (len(subs) > 0):
            choice = 1

        else:
            print('No subtitles found! Exiting.')
            sys.exit(0)
            
        # Index is 1 less than the choice value
        ind = choice - 1

        # Get the url of the subtitle
        sub_url = subs[ind]['SubDownloadLink']
        r = requests.get(sub_url)

        # Download the subtitle
        with open(subs[ind]['SubFileName'],'wb') as f:
            
            print ("Downloading %s" % (subs[ind]['SubFileName']))
            response = requests.get(sub_url, stream=True)
            total_length = response.headers.get('content-length')

            if total_length is None: # no content length header
                f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s] %d%%" % ('=' * done, ' ' * (50-done), done * 2) )    
                    sys.stdout.flush()


if __name__ == '__main__':
    main()