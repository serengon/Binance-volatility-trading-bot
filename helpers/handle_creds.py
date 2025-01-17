def load_correct_creds(creds):
    return creds['prod']['access_key'], creds['prod']['secret_key']





def test_api_key(client, BinanceAPIException):
    """Checks to see if API keys supplied returns errors

    Args:
        client (class): binance client class
        BinanceAPIException (clas): binance exeptions class

    Returns:
        bool | msg: true/false depending on success, and message
    """
    try:
        client.get_account()
        return True, "API key validated succesfully"
    
    except BinanceAPIException as e:   
    
      
        if e.code == -2015:
            msg = "Your API key is not formatted correctly..."

        elif e.code == -2014:
            america = "If you are in america, you will have to update your TLD to use 'us'."
            ip_b = "If you set an IP block on your keys make sure this IP address is allowed. check ipinfo.io/ip"
            bad_key = "Your API key is not formatted correctly..."
            msg = f"Your API key is either incorrect, IP blocked, or incorrect tld/permissons...\n  most likely: {bad_key}\n  {america}\n  {ip_b}"

        elif e.code == -2021:
            issue = "https://github.com/CyberPunkMetalHead/Binance-volatility-trading-bot/issues/28"
            desc = "Ensure your OS is time synced with a timeserver. See issue."
            msg = f"Timestamp for this request was 1000ms ahead of the server's time.\n  {issue}\n  {desc}"
        
        else:
            msg = e

        return False, msg
    
    except Exception as e:
        return False, f"Fallback exception occured:\n{e}"
