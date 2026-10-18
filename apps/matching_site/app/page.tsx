import {getChatGPTUser,chatGPTSignInPath,chatGPTSignOutPath} from './chatgpt-auth';
import SiteApp from './site-app';
export const dynamic='force-dynamic';
export default async function Home(){
 const user=await getChatGPTUser();
 return <SiteApp signedIn={!!user} accountHref={user?chatGPTSignOutPath('/'):chatGPTSignInPath('/')}/>;
}
