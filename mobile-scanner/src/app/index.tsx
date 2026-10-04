import {Redirect} from 'expo-router';
import {ActivityIndicator} from 'react-native';
import {useSession} from '../session';
export default function Index(){const s=useSession();if(!s.ready)return <ActivityIndicator/>;return <Redirect href={s.login?'/staff/stock':'/login'}/>}
