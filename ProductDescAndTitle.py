import openai
import os
import key
import pandas as pd
import csv
from tqdm import tqdm
import math
from ratelimiter import RateLimiter

openai.api_key = key.key

# =============================================================================
# Parent class for sending request and managing response
# =============================================================================
class SendRequest(object):
    # Constructor
    def __init__(self, title):
        self.title = title
    
    @RateLimiter(max_calls=55, period=1)
    def getResponse(self, prompt):
        nothing = ''
        try:
            # using gpt-3.5-turbo chat-gpt model
            completion = openai.ChatCompletion.create(
              model="gpt-3.5-turbo",  
              messages=[
                {"role": "user", "content": prompt}
              ]
            )
            # API response
            return completion.choices[0].message.content
        # Handling different exceptions
        except openai.error.APIError as e:
            print(f"OpenAI API returned an API Error: {e}")
            return nothing
        except openai.error.APIConnectionError as e:
            print(f"Failed to connect to OpenAI API: {e}")
            return nothing
        except openai.error.RateLimitError as e:
            print(f"OpenAI API request exceeded rate limit: {e}")
            return nothing
        except openai.error.Timeout as e:
            print(f"OpenAI API request timed out: {e}")
            return nothing
        except openai.error.InvalidRequestError as e:
            print(f"Invalid request to OpenAI API: {e}")
            return nothing
        except openai.error.AuthenticationError as e:
            print(f"Authentication error with OpenAI API: {e}")
            return nothing
        except openai.error.ServiceUnavailableError as e:
            print(f"OpenAI API service unavailable: {e}")
            return nothing        
        except:
            return nothing
        
    
    def getDescription(self):
        prompt = """I would like to give you """+self.title+"""and I would like you to write a seo optimized
        Product description and a search engine Meta description that will rank on the first page of
        google"""
        
        res = self.getResponse(prompt)
        if res != '':
            return res
        else:
            res = self.getResponse(prompt)    
            return res
        return

    # To check if this person is an employee
    def getUniqueTitle(self):
        prompt = """Product tile prompt
                    The purpose of this prompt is to eliminate duplicate content on my website. 
                    I have products that have similar attributes and therefore the same product titles. 
                    I would like to provide you with the title of a product and I would like you to seo 
                    optimize it for google and make all the product titles unique so there is not duplicate
                    content in the titles. I would also like you to just provide me one answer that you recommend.
                    please only provide me your answer and nothing else."""+self.title
        
        res = self.getResponse(prompt)
        if res != '':
            return res
        else:
            res = self.getResponse(prompt)    
            return res
        return

# =============================================================================
# Child class for getting data from parent and process that data further
# =============================================================================
class GET_DATA(SendRequest):
    def __init__(self, path): 
        self.pth = path
        self.Opth = 'Results.csv' 
        self.main()
        
    def red_excel(self, pth):
        data = pd.read_excel(pth, index_col=False)
        
        prod_data = []
        # loop through rows of excel
        for i, pro in data.iterrows():
            dic = {"Handle":pro['Handle'], "Title":pro['Title']}
            if dic not in prod_data:
                # append Prod ID, Handle, and Title to prod_data variable
                prod_data.append(dic) 
            
        return prod_data
    
    def prepareDescAndMeta(self, txt):
        text = ''
        txt = txt.replace('\n', ' ')
        start = 0
        N = 10
        l = txt.split()
        for stop in range(N, len(l)+N, N):
            text += ' '.join(l[start:stop])
            text += ' \n '
            start = stop    
        return str(text)
    
    def getDesAndMeta(self, title):
        des = SendRequest(title).getDescription()
        
        # split the whole response by new lines
        split_des = des.split('\n')    
        ind = []
        # iterate through the list of response
        for str_ in split_des:
            # search for headings 
            if str_.strip().endswith(':') and ('Product Description' in str_ or 'Meta Description' in str_):
                # append headings indexes to ind variable
                ind.append(split_des.index(str_))
        # get saperate text for both headings
        desc = ' '.join(split_des[ind[0]+1:ind[-1]])
        meta = ' '.join(split_des[ind[-1]+1: ])
        
        DESC = self.prepareDescAndMeta(desc)
        META = self.prepareDescAndMeta(meta)
        return DESC, META
    
    def getUniTitle(self, title):
        TITLE = SendRequest(title).getUniqueTitle()
        
        text = TITLE.replace('"', '')
        txt = text.replace("'", '')
        
        return txt
        
    
    def main(self):
        Title = self.red_excel(self.pth)
        outp = self.Opth
        
        # Headings or first row elements
        header = ["Handle", "Title", "Seo Optimized Product TITLE", "Seo Optimized Product Description", 
                  "Seo Optimized Google Meta Search engine Description", "Failed"]

        with open(outp, 'w', encoding="utf-8", newline = '') as output_csv:
            # initialize rows writer
            csv_writer = csv.writer(output_csv)
            # write headers to the file
            csv_writer.writerow(header)
            for l in tqdm(Title):
                TITLE = ''
                nan = ''
                desc = ''
                meta_data = ''
                try:
                  if math.isnan(l['Title']):
                      nan = True
                except:
                      nan = False
                if nan:
                    print('Error while processing: ', l['Title'])
                    lst = [l["Handle"], l['Title'], TITLE, desc, meta_data, 'REDO']
                    csv_writer.writerow(lst)
                else:
                    try:
                        TITLE = self.getUniTitle(l['Title'])
                        desc, meta_data = self.getDesAndMeta(l['Title'])
                        if TITLE and desc and meta_data:
                            lst = [l["Handle"], l['Title'], TITLE, desc, meta_data, '']
                            csv_writer.writerow(lst)
                            print('Row Added')
                        else:
                            print('Error while processing: ', l['Title'])
                            lst = [l["Handle"], l['Title'], TITLE, desc, meta_data, 'REDO']
                            csv_writer.writerow(lst)
                    except :
                        print('Error while processing: ', l['Title'])
                        lst = [l["Handle"], l['Title'], TITLE, desc, meta_data, 'REDO']
                        csv_writer.writerow(lst)
                    finally:
                        pass
        return
    
    
