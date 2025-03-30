import sys, os, json
from playwright_manager import *


def runcmd(cmd):
    print('------------------------------------------------------------')
    print(cmd)
    res=os.popen(cmd).read()
    print(res)
    print('------------------------------------------------------------')
    return(res)



# res=runcmd("/usr/bin/python3 playwright_manager.py")


async def main():
    """Main function to test different browser modes"""
    # Test Chromium mode
    await test_chromium_mode()
    
    # Test Browserbase mode
    #await test_browserbase_mode()

if __name__ == "__main__":
    # runcmd("git restore ../../../shopping.json")
    # runcmd("git pull ")
    
    try:
        asyncio.run(main())
        print("cookie valid ")
    except Exception as err:
        print("cookie invalid. will update")
        runcmd("rm ../../../shopping.json")
        asyncio.run(main())
        runcmd("git add ../../../shopping.json")
        runcmd("git commit -m 'update cookie'")
        runcmd("git push ")
    
    print("done!!!")



