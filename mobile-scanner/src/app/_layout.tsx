import {Stack} from 'expo-router';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import {SessionProvider} from '../session';
export default function Layout(){return <SafeAreaProvider><SessionProvider><Stack screenOptions={{headerShown:false}}/></SessionProvider></SafeAreaProvider>}
